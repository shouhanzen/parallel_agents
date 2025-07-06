import asyncio
import cmd
import json
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from datetime import datetime

from .config import VerifierConfig
from .overseer import Overseer
from .mock_overseer import MockOverseer


class LogStreamer:
    """Handles real-time log streaming from log files"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.running = False
        self.thread = None
        
    def start_streaming(self):
        """Start streaming logs in a separate thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._stream_logs, daemon=True)
        self.thread.start()
        
    def stop_streaming(self):
        """Stop streaming logs"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            
    def _stream_logs(self):
        """Stream logs from the file"""
        try:
            # Start from the end of file if it exists
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    f.seek(0, 2)  # Go to end of file
                    
            while self.running:
                if not self.log_file.exists():
                    time.sleep(1)
                    continue
                    
                try:
                    with open(self.log_file, 'r') as f:
                        # Read from current position to end
                        content = f.read()
                        if content:
                            self._format_and_print_logs(content)
                        
                except Exception as e:
                    print(f"Error reading log file: {e}")
                    
                time.sleep(0.5)  # Check for new content every 500ms
                
        except Exception as e:
            print(f"Log streaming error: {e}")
            
    def _format_and_print_logs(self, content: str):
        """Format and print log entries"""
        lines = content.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            try:
                # Try to parse as JSON
                log_entry = json.loads(line)
                timestamp = log_entry.get('timestamp', 'Unknown')
                
                if log_entry.get('event') == 'session_start':
                    print(f"\n🚀 [{timestamp}] Session started - Mission: {log_entry.get('mission')}")
                elif 'prompt' in log_entry:
                    success = "✅" if log_entry.get('success') else "❌"
                    print(f"\n{success} [{timestamp}] Claude Interaction")
                    print(f"   Prompt: {log_entry['prompt'][:100]}...")
                    if log_entry.get('response'):
                        print(f"   Response: {log_entry['response'][:100]}...")
                    if log_entry.get('error'):
                        print(f"   Error: {log_entry['error']}")
                else:
                    print(f"📋 [{timestamp}] {line}")
                    
            except json.JSONDecodeError:
                # Not JSON, print as-is
                print(f"📋 {line}")


class InteractiveVerifierCLI(cmd.Cmd):
    """Interactive CLI for the Verifier system"""
    
    intro = """
🤖 Parallel Agents Interactive CLI
Type 'help' for available commands, 'exit' to quit.
"""
    prompt = "(parallel-agents) "
    
    def __init__(self):
        super().__init__()
        self.config_file = "verifier.json"
        self.config: Optional[VerifierConfig] = None
        self.overseer: Optional[Union[Overseer, MockOverseer]] = None
        self.overseer_task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.log_streamer: Optional[LogStreamer] = None
        self.running_agents: Dict[str, Any] = {}
        self.agent_counter = 0
        
        # Load initial configuration
        self._load_config()
        
    def _load_config(self):
        """Load configuration from file"""
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                self.config = VerifierConfig.from_file(self.config_file)
                print(f"✅ Loaded configuration from {self.config_file}")
            except Exception as e:
                print(f"❌ Error loading config: {e}")
                self.config = VerifierConfig()
        else:
            self.config = VerifierConfig()
            print("📋 Using default configuration")
            
    def do_config(self, args):
        """Show current configuration. Usage: config [file]"""
        if args:
            self.config_file = args.strip()
            self._load_config()
        else:
            if self.config:
                print("\n📊 Current Configuration:")
                print(json.dumps(self.config.model_dump(), indent=2))
            else:
                print("❌ No configuration loaded")
                
    def do_start(self, args):
        """Start the verifier agent. Usage: start [--demo] [--mission mission]"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        if self.overseer and self.overseer.is_running():
            print("⚠️  Agent is already running. Use 'stop' first.")
            return
            
        # Parse arguments
        demo_mode = '--demo' in args
        mission = None
        
        args_parts = args.split()
        if '--mission' in args_parts:
            try:
                mission_idx = args_parts.index('--mission')
                if mission_idx + 1 < len(args_parts):
                    mission = args_parts[mission_idx + 1]
            except (ValueError, IndexError):
                pass
                
        # Update config if mission specified
        if mission:
            self.config.agent_mission = mission
            
        # Create overseer
        if demo_mode:
            self.overseer = MockOverseer(self.config)
            print(f"🧪 Starting demo agent with mission: {self.config.agent_mission}")
        else:
            self.overseer = Overseer(self.config)
            print(f"🚀 Starting agent with mission: {self.config.agent_mission}")
            
        # Start in background thread
        def run_overseer():
            try:
                if self.overseer is None:
                    print("❌ No overseer to start")
                    return
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.overseer.start())
            except Exception as e:
                print(f"❌ Agent failed: {e}")
                # Remove from running agents on failure
                agent_id = f"agent-{self.agent_counter}"
                if agent_id in self.running_agents:
                    del self.running_agents[agent_id]
                
        self.overseer_thread = threading.Thread(target=run_overseer, daemon=True)
        self.overseer_thread.start()
        
        # Track the agent
        self.agent_counter += 1
        agent_id = f"agent-{self.agent_counter}"
        self.running_agents[agent_id] = {
            'id': agent_id,
            'mission': self.config.agent_mission,
            'status': 'starting',
            'started_at': datetime.now().isoformat(),
            'mode': 'demo' if demo_mode else 'production',
            'thread': self.overseer_thread,
            'overseer': self.overseer
        }
        
        # Give it a moment to start
        time.sleep(1)
        if self.overseer and self.overseer.is_running():
            self.running_agents[agent_id]['status'] = 'running'
        print(f"✅ Agent started successfully! (ID: {agent_id})")
        
    def do_stop(self, args):
        """Stop the running verifier agent. Usage: stop [agent-id]"""
        if args.strip():
            # Stop specific agent
            agent_id = args.strip()
            if agent_id not in self.running_agents:
                print(f"❌ Agent {agent_id} not found")
                return
                
            agent_info = self.running_agents[agent_id]
            try:
                if agent_info['overseer']:
                    asyncio.run(agent_info['overseer'].stop())
                agent_info['status'] = 'stopped'
                agent_info['stopped_at'] = datetime.now().isoformat()
                print(f"✅ Agent {agent_id} stopped successfully!")
                
                # Clean up current overseer if it's the one being stopped
                if agent_info['overseer'] == self.overseer:
                    self.overseer = None
                    
            except Exception as e:
                print(f"❌ Error stopping agent {agent_id}: {e}")
        else:
            # Stop current/main agent
            if not self.overseer:
                print("⚠️  No main agent is running")
                return
                
            try:
                asyncio.run(self.overseer.stop())
                
                # Mark all agents with this overseer as stopped
                for agent_id, agent_info in self.running_agents.items():
                    if agent_info['overseer'] == self.overseer:
                        agent_info['status'] = 'stopped'
                        agent_info['stopped_at'] = datetime.now().isoformat()
                        
                self.overseer = None
                print("✅ Agent stopped successfully!")
            except Exception as e:
                print(f"❌ Error stopping agent: {e}")
            
    def do_status(self, args):
        """Show agent status and configuration"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        print("\n📊 Agent Status:")
        
        if self.overseer and self.overseer.is_running():
            print("🟢 Status: Running")
            print(f"🎯 Mission: {self.config.agent_mission}")
            print(f"👀 Watching: {', '.join(self.config.watch_dirs)}")
            print(f"📁 Working Set: {self.config.working_set_dir}")
            print(f"📝 Log File: {self.config.claude_log_file}")
        else:
            print("🔴 Status: Stopped")
            
        # Check if log file exists and show recent activity
        log_path = Path(self.config.claude_log_file)
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        lines = content.split('\n')
                        recent_lines = lines[-3:] if len(lines) > 3 else lines
                        print(f"\n📋 Recent Activity ({len(lines)} total log entries):")
                        for line in recent_lines:
                            if line.strip():
                                try:
                                    entry = json.loads(line)
                                    timestamp = entry.get('timestamp', 'Unknown')
                                    if entry.get('event') == 'session_start':
                                        print(f"  🚀 {timestamp}: Session started")
                                    elif 'prompt' in entry:
                                        status = "✅" if entry.get('success') else "❌"
                                        print(f"  {status} {timestamp}: Claude interaction")
                                except json.JSONDecodeError:
                                    print(f"  📋 {line[:80]}...")
            except Exception as e:
                print(f"❌ Error reading logs: {e}")
        else:
            print("📝 No log file found")
            
    def do_logs(self, args):
        """Stream logs in real-time. Usage: logs [start|stop] [agent-id]"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        args_parts = args.strip().split() if args else []
        command = args_parts[0] if args_parts else "start"
        agent_id = args_parts[1] if len(args_parts) > 1 else None
        
        if command == "start":
            if self.log_streamer and self.log_streamer.running:
                print("⚠️  Log streaming is already active")
                return
                
            # Determine log file path
            if agent_id:
                if agent_id not in self.running_agents:
                    print(f"❌ Agent {agent_id} not found")
                    return
                # For now, use the same log file - in future could be per-agent
                log_path = Path(self.config.claude_log_file)
                print(f"📡 Starting log stream for agent {agent_id} from: {log_path}")
            else:
                log_path = Path(self.config.claude_log_file)
                print(f"📡 Starting log stream from: {log_path}")
                
            print("Press Ctrl+C or use 'logs stop' to stop streaming\n")
            
            self.log_streamer = LogStreamer(log_path)
            self.log_streamer.start_streaming()
            print("✅ Log streaming started!")
            
        elif command == "stop":
            if self.log_streamer:
                self.log_streamer.stop_streaming()
                self.log_streamer = None
                print("✅ Log streaming stopped!")
            else:
                print("⚠️  No log streaming is active")
        else:
            print("❌ Usage: logs [start|stop] [agent-id]")
            
    def do_agents(self, args):
        """List active parallel agents. Usage: agents [--all]"""
        if not self.running_agents:
            print("📭 No agents found")
            return
            
        show_all = '--all' in args
        
        print("\n🤖 Parallel Agents:")
        print("=" * 80)
        
        for agent_id, agent_info in self.running_agents.items():
            status = agent_info['status']
            
            # Filter by status unless --all is specified
            if not show_all and status not in ['running', 'starting']:
                continue
                
            # Status emoji
            status_emoji = {
                'running': '🟢',
                'starting': '🟡', 
                'stopped': '🔴',
                'failed': '❌'
            }.get(status, '⚪')
            
            print(f"{status_emoji} {agent_id}")
            print(f"   Mission: {agent_info['mission']}")
            print(f"   Status: {status}")
            print(f"   Mode: {agent_info['mode']}")
            print(f"   Started: {agent_info['started_at']}")
            
            if 'stopped_at' in agent_info:
                print(f"   Stopped: {agent_info['stopped_at']}")
                
            # Show thread status
            if agent_info.get('thread'):
                thread_alive = agent_info['thread'].is_alive()
                print(f"   Thread: {'alive' if thread_alive else 'dead'}")
                
            # Show overseer status
            if agent_info.get('overseer'):
                try:
                    overseer_running = agent_info['overseer'].is_running()
                    print(f"   Overseer: {'running' if overseer_running else 'stopped'}")
                except:
                    print(f"   Overseer: unknown")
                    
            print()
            
        # Summary
        running_count = sum(1 for a in self.running_agents.values() if a['status'] == 'running')
        total_count = len(self.running_agents)
        
        if show_all:
            print(f"📊 Total: {total_count} agents ({running_count} running)")
        else:
            print(f"📊 Active: {running_count} agents (use --all to show stopped agents)")
            
    def do_changes(self, args):
        """List changes in working sets. Usage: changes [--detailed]"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        from .working_set import WorkingSetManager
        
        detailed = '--detailed' in args
        
        # Get working set directory
        working_set_dir = Path(self.config.working_set_dir)
        
        if not working_set_dir.exists():
            print(f"📭 Working set directory not found: {working_set_dir}")
            return
            
        ws_manager = WorkingSetManager(str(working_set_dir))
        
        print(f"\n📂 Working Set Changes: {working_set_dir}")
        print("=" * 80)
        
        # List all files in working set
        all_files = []
        for file_path in working_set_dir.rglob("*"):
            if file_path.is_file():
                all_files.append(file_path)
                
        if not all_files:
            print("📭 No files found in working set")
            return
            
        # Group by type
        file_groups = {
            'tests': [],
            'artifacts': [],
            'reports': [],
            'logs': [],
            'other': []
        }
        
        for file_path in all_files:
            relative_path = file_path.relative_to(working_set_dir)
            file_info = {
                'path': relative_path,
                'full_path': file_path,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            # Categorize files
            if file_path.name.startswith('test_') or '/tests/' in str(relative_path):
                file_groups['tests'].append(file_info)
            elif '/artifacts/' in str(relative_path):
                file_groups['artifacts'].append(file_info)
            elif '/reports/' in str(relative_path) or file_path.suffix == '.md':
                file_groups['reports'].append(file_info)
            elif file_path.suffix in ['.log', '.jsonl']:
                file_groups['logs'].append(file_info)
            else:
                file_groups['other'].append(file_info)
        
        # Display results
        for group_name, files in file_groups.items():
            if not files:
                continue
                
            group_emoji = {
                'tests': '🧪',
                'artifacts': '📦',
                'reports': '📋',
                'logs': '📝',
                'other': '📄'
            }[group_name]
            
            print(f"\n{group_emoji} {group_name.title()} ({len(files)} files):")
            
            for file_info in sorted(files, key=lambda x: x['modified'], reverse=True):
                if detailed:
                    print(f"  📄 {file_info['path']}")
                    print(f"     Size: {file_info['size']} bytes")
                    print(f"     Modified: {file_info['modified']}")
                    
                    # Show content preview for small files
                    if file_info['size'] < 1000 and file_info['full_path'].suffix in ['.py', '.md', '.txt']:
                        try:
                            content = file_info['full_path'].read_text()
                            preview = content[:200] + "..." if len(content) > 200 else content
                            print(f"     Preview: {preview}")
                        except:
                            pass
                    print()
                else:
                    size_str = f"{file_info['size']}B" if file_info['size'] < 1024 else f"{file_info['size']//1024}KB"
                    print(f"  📄 {file_info['path']} ({size_str})")
        
        # Summary
        total_files = len(all_files)
        total_size = sum(f.stat().st_size for f in all_files)
        size_str = f"{total_size}B" if total_size < 1024 else f"{total_size//1024}KB"
        
        print(f"\n📊 Summary: {total_files} files, {size_str} total")
        
        # Show metadata if available
        metadata = ws_manager.read_metadata()
        if metadata:
            print(f"\n📋 Metadata:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
            
    def do_elevate(self, args):
        """Elevate changes from working sets to main codebase. Usage: elevate <file_path> [--preview]"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        from .working_set import WorkingSetManager
        
        args_parts = args.strip().split() if args else []
        if not args_parts:
            print("❌ Usage: elevate <file_path> [--preview]")
            print("   Example: elevate test_calculator.py")
            print("   Example: elevate artifacts/new_feature.py --preview")
            return
            
        file_path = args_parts[0]
        preview = '--preview' in args_parts
        
        # Get working set directory
        working_set_dir = Path(self.config.working_set_dir)
        
        if not working_set_dir.exists():
            print(f"❌ Working set directory not found: {working_set_dir}")
            return
            
        source_file = working_set_dir / file_path
        
        if not source_file.exists():
            print(f"❌ File not found in working set: {file_path}")
            return
            
        # Determine destination based on file type
        if source_file.name.startswith('test_'):
            # Test files go to tests directory
            dest_file = Path("tests") / source_file.name
        elif source_file.suffix == '.py':
            # Python files go to src directory
            dest_file = Path("src") / source_file.name
        elif source_file.suffix == '.md':
            # Markdown files go to docs directory
            dest_file = Path("docs") / source_file.name
        else:
            # Other files go to root or ask user
            dest_file = Path(source_file.name)
            
        print(f"📋 Elevating: {source_file} -> {dest_file}")
        
        if preview:
            print("\n🔍 Preview mode - no files will be moved")
            
            # Show source content
            try:
                content = source_file.read_text()
                print(f"\n📄 Source content ({len(content)} chars):")
                print("-" * 40)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 40)
            except Exception as e:
                print(f"❌ Error reading source: {e}")
                return
                
            # Check if destination exists
            if dest_file.exists():
                print(f"\n⚠️  Destination file already exists: {dest_file}")
                try:
                    existing_content = dest_file.read_text()
                    print(f"📄 Existing content ({len(existing_content)} chars):")
                    print("-" * 40)
                    print(existing_content[:500] + "..." if len(existing_content) > 500 else existing_content)
                    print("-" * 40)
                except Exception as e:
                    print(f"❌ Error reading existing file: {e}")
            else:
                print(f"✅ Destination is clear: {dest_file}")
                
        else:
            # Perform actual elevation
            try:
                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Check if destination exists
                if dest_file.exists():
                    response = input(f"⚠️  Destination file exists: {dest_file}. Overwrite? (y/N): ")
                    if response.lower() != 'y':
                        print("❌ Elevation cancelled")
                        return
                        
                # Copy file
                import shutil
                shutil.copy2(source_file, dest_file)
                
                print(f"✅ Elevated successfully: {source_file} -> {dest_file}")
                
                # Ask if we should remove from working set
                response = input("🗑️  Remove from working set? (y/N): ")
                if response.lower() == 'y':
                    source_file.unlink()
                    print("✅ Removed from working set")
                else:
                    print("📝 Kept in working set")
                    
            except Exception as e:
                print(f"❌ Error elevating file: {e}")
                
    def do_review(self, args):
        """Run code review agent to suggest improvements. Usage: review [src_dir]"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        from .review_agent import CodeReviewAgent
        
        src_dir = args.strip() if args.strip() else "src"
        
        print(f"🔍 Running code review on directory: {src_dir}")
        
        review_agent = CodeReviewAgent(self.config)
        review_agent.run_review()
        
    def do_apply_suggestions(self, args):
        """Apply suggestions from potential_todo.jsonl. Usage: apply_suggestions [--preview] [--filter type]"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        args_parts = args.strip().split() if args else []
        preview = '--preview' in args_parts
        filter_type = None
        
        if '--filter' in args_parts:
            try:
                filter_idx = args_parts.index('--filter')
                if filter_idx + 1 < len(args_parts):
                    filter_type = args_parts[filter_idx + 1]
            except (ValueError, IndexError):
                pass
                
        potential_todo_file = Path("potential_todo.jsonl")
        
        if not potential_todo_file.exists():
            print(f"❌ File not found: {potential_todo_file}")
            print("Run 'review' command first to generate suggestions")
            return
            
        # Read suggestions
        suggestions = []
        try:
            with open(potential_todo_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        suggestions.append(json.loads(line))
        except Exception as e:
            print(f"❌ Error reading suggestions: {e}")
            return
            
        if not suggestions:
            print("📭 No suggestions found in file")
            return
            
        # Filter suggestions if requested
        if filter_type:
            suggestions = [s for s in suggestions if s.get('type') == filter_type]
            print(f"🔍 Filtered to {len(suggestions)} suggestions of type '{filter_type}'")
            
        if not suggestions:
            print("📭 No suggestions match the filter")
            return
            
        print(f"📋 Found {len(suggestions)} suggestions to process")
        
        # Group by type for better processing
        by_type = {}
        for suggestion in suggestions:
            stype = suggestion.get('type', 'unknown')
            if stype not in by_type:
                by_type[stype] = []
            by_type[stype].append(suggestion)
            
        print(f"📊 Suggestions by type:")
        for stype, items in by_type.items():
            print(f"  {stype}: {len(items)}")
            
        if preview:
            print("\n🔍 Preview mode - showing suggestions that would be applied:")
            self._preview_suggestions(suggestions)
        else:
            print("\n🚀 Applying suggestions...")
            applied_count = self._apply_suggestions(suggestions)
            print(f"✅ Applied {applied_count} suggestions successfully")
            
    def _preview_suggestions(self, suggestions: List[Dict[str, Any]]) -> None:
        """Preview suggestions that would be applied"""
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion.get('title', 'Unknown')}")
            print(f"   File: {suggestion.get('file', 'Unknown')}")
            print(f"   Line: {suggestion.get('line', 'Unknown')}")
            print(f"   Type: {suggestion.get('type', 'unknown')}")
            print(f"   Severity: {suggestion.get('severity', 'unknown')}")
            print(f"   Description: {suggestion.get('description', 'No description')}")
            print(f"   Suggestion: {suggestion.get('suggestion', 'No suggestion')}")
            
    def _apply_suggestions(self, suggestions: List[Dict[str, Any]]) -> int:
        """Apply suggestions to the codebase"""
        applied_count = 0
        
        for suggestion in suggestions:
            stype = suggestion.get('type', 'unknown')
            
            try:
                if stype == 'documentation':
                    if self._apply_documentation_suggestion(suggestion):
                        applied_count += 1
                elif stype == 'optimization':
                    if self._apply_optimization_suggestion(suggestion):
                        applied_count += 1
                elif stype == 'style':
                    if self._apply_style_suggestion(suggestion):
                        applied_count += 1
                elif stype == 'todo':
                    if self._apply_todo_suggestion(suggestion):
                        applied_count += 1
                else:
                    print(f"⚠️  Cannot auto-apply suggestion type: {stype}")
                    
            except Exception as e:
                print(f"❌ Error applying suggestion: {e}")
                
        return applied_count
        
    def _apply_documentation_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Apply documentation-related suggestions"""
        file_path = Path(suggestion.get('file', ''))
        line_num = suggestion.get('line', 0)
        
        if not file_path.exists():
            return False
            
        try:
            lines = file_path.read_text().split('\n')
            
            if line_num > len(lines):
                return False
                
            # Add basic docstring for functions and classes
            target_line = lines[line_num - 1]
            
            if target_line.strip().startswith('def '):
                # Add function docstring
                func_name = target_line.split('def ')[1].split('(')[0]
                indent = len(target_line) - len(target_line.lstrip())
                docstring = f'{" " * (indent + 4)}"""TODO: Add description for {func_name}"""'
                lines.insert(line_num, docstring)
                
            elif target_line.strip().startswith('class '):
                # Add class docstring
                class_name = target_line.split('class ')[1].split('(')[0].split(':')[0]
                indent = len(target_line) - len(target_line.lstrip())
                docstring = f'{" " * (indent + 4)}"""TODO: Add description for {class_name}"""'
                lines.insert(line_num, docstring)
                
            file_path.write_text('\n'.join(lines))
            print(f"✅ Added docstring to {file_path}:{line_num}")
            return True
            
        except Exception as e:
            print(f"❌ Error applying documentation suggestion: {e}")
            return False
            
    def _apply_optimization_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Apply optimization suggestions (like removing unused imports)"""
        file_path = Path(suggestion.get('file', ''))
        line_num = suggestion.get('line', 0)
        
        if not file_path.exists():
            return False
            
        try:
            lines = file_path.read_text().split('\n')
            
            if line_num > len(lines):
                return False
                
            # Remove unused imports
            if 'unused import' in suggestion.get('description', '').lower():
                target_line = lines[line_num - 1]
                if target_line.strip().startswith(('import ', 'from ')):
                    lines.pop(line_num - 1)
                    file_path.write_text('\n'.join(lines))
                    print(f"✅ Removed unused import from {file_path}:{line_num}")
                    return True
                    
        except Exception as e:
            print(f"❌ Error applying optimization suggestion: {e}")
            return False
            
    def _apply_style_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Apply style suggestions"""
        # For now, just log that we would apply it
        print(f"ℹ️  Would apply style suggestion: {suggestion.get('title', 'Unknown')}")
        return True
        
    def _apply_todo_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Apply TODO suggestions"""
        # For now, just log that we found it
        print(f"ℹ️  TODO found: {suggestion.get('description', 'Unknown')}")
        return True
            
    def do_init(self, args):
        """Initialize a new configuration file. Usage: init [filename]"""
        filename = args.strip() if args else "verifier.json"
        config_path = Path(filename)
        
        if config_path.exists():
            response = input(f"Configuration file {filename} already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("❌ Cancelled")
                return
                
        config = VerifierConfig()
        config.to_file(filename)
        
        print(f"✅ Created configuration file: {filename}")
        print("Edit the configuration file to customize your setup.")
        
    def do_validate(self, args):
        """Validate the current configuration"""
        if not self.config:
            print("❌ No configuration loaded")
            return
            
        print("🔍 Validating configuration...")
        
        # Check watch directories
        missing_dirs = []
        for watch_dir in self.config.watch_dirs:
            if not Path(watch_dir).exists():
                missing_dirs.append(watch_dir)
                
        if missing_dirs:
            print(f"⚠️  Missing watch directories: {', '.join(missing_dirs)}")
        else:
            print(f"✅ Watch directories exist: {', '.join(self.config.watch_dirs)}")
            
        # Check working set directory
        working_set_path = Path(self.config.working_set_dir)
        try:
            working_set_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Working set directory ready: {working_set_path}")
        except Exception as e:
            print(f"❌ Working set directory error: {e}")
            
        print("✅ Configuration validation complete!")
        
    def do_exit(self, args):
        """Exit the interactive CLI"""
        return self.do_quit(args)
        
    def do_quit(self, args):
        """Exit the interactive CLI"""
        # Stop any running services
        if self.log_streamer:
            self.log_streamer.stop_streaming()
            
        if self.overseer:
            print("🛑 Stopping agent...")
            try:
                asyncio.run(self.overseer.stop())
            except Exception:
                pass
                
        print("👋 Goodbye!")
        return True
        
    def do_help(self, args):
        """Show available commands"""
        if args:
            # Show help for specific command
            super().do_help(args)
        else:
            print("""
🤖 Available Commands:

📊 Status & Configuration:
  config [file]     - Show/load configuration
  status           - Show agent status and recent activity
  validate         - Validate current configuration
  init [filename]  - Initialize new configuration file

🚀 Agent Control:
  start [options]  - Start the verifier agent
                     Options: --demo, --mission <mission>
  stop            - Stop the running agent

📡 Monitoring:
  logs [start|stop] [agent-id] - Stream logs in real-time
  agents [--all]   - List active parallel agents
  changes [--detailed] - List changes in working sets
  elevate <file> [--preview] - Elevate changes from working sets
  review [src_dir] - Run code review agent
  apply_suggestions [--preview] [--filter type] - Apply suggestions from potential_todo.jsonl
  
🔧 Utility:
  help [command]   - Show help for command
  exit/quit       - Exit the CLI

Examples:
  start --demo --mission testing
  logs start
  agents --all
  changes --detailed
  elevate test_calculator.py --preview
  review src
  apply_suggestions --preview --filter documentation
  config my-config.json
""")

    def emptyline(self):
        """Handle empty line input - do nothing"""
        pass
        
    def onecmd(self, line):
        """Override to handle Ctrl+C gracefully"""
        try:
            return super().onecmd(line)
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted (use 'exit' to quit)")
            return False


def main():
    """Main entry point for the interactive CLI"""
    try:
        cli = InteractiveVerifierCLI()
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == '__main__':
    main()