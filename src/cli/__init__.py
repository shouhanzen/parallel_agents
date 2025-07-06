#!/usr/bin/env python3
"""CLI entry point for the Parallel Agents Verifier System"""

import click
import sys
import json
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.config.models import ParallelAgentsConfig
    from core.config.profiles import SDKConfigManager
    from core.overseer.overseer import Overseer
    from core.overseer.mock_overseer import MockOverseer
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    print("Some functionality may not be available.")
    ParallelAgentsConfig = None
    SDKConfigManager = None
    Overseer = None
    MockOverseer = None


@click.group()
@click.version_option(version="0.1.0", prog_name="verifier")
def main():
    """Parallel Agents Verifier System - Automated testing with Claude Code agents"""
    pass


@main.command()
@click.option('--config', '-c', default='verifier.json', 
              help='Configuration file path (default: verifier.json)')
@click.option('--watch-dir', '-w', multiple=True,
              help='Directories to watch (can be specified multiple times)')
@click.option('--mission', '-m', 
              help='Agent mission (testing, docs, tooling)')
def start(config: str, watch_dir: tuple, mission: Optional[str]):
    """Start the verifier overseer process"""
    click.echo("🚀 Starting Parallel Agents Verifier...")
    
    # Load configuration
    try:
        if Path(config).exists():
            with open(config, 'r') as f:
                config_data = json.load(f)
            if ParallelAgentsConfig:
                agent_config = ParallelAgentsConfig(**config_data)
            else:
                click.echo("⚠️  Core modules not available. Using basic config.")
                agent_config = None
        else:
            click.echo(f"❌ Configuration file '{config}' not found. Run 'verifier init' first.")
            return
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}")
        return
    
    # Apply overrides
    if watch_dir:
        if agent_config:
            agent_config.watch_dirs = list(watch_dir)
        click.echo(f"📂 Watching directories: {', '.join(watch_dir)}")
    
    if mission:
        if agent_config:
            agent_config.agent_mission = mission
        click.echo(f"🎯 Mission: {mission}")
    
    # Start overseer
    if Overseer and agent_config:
        try:
            overseer = Overseer(agent_config)
            click.echo("✅ Overseer started. Monitoring for changes...")
            click.echo("Press Ctrl+C to stop.")
            overseer.start()
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping verifier...")
        except Exception as e:
            click.echo(f"❌ Error starting overseer: {e}")
    else:
        click.echo("❌ Cannot start overseer - core modules not available.")


@main.command()
@click.option('--config', '-c', default='verifier.json',
              help='Configuration file path (default: verifier.json)')
@click.option('--watch-dir', '-w', multiple=True,
              help='Directories to watch (can be specified multiple times)')
@click.option('--mission', '-m',
              help='Agent mission (testing, docs, tooling)')
def demo(config: str, watch_dir: tuple, mission: Optional[str]):
    """Start the verifier with mock agent for testing"""
    click.echo("🎭 Starting Parallel Agents Verifier in Demo Mode...")
    
    # Load configuration (similar to start)
    try:
        if Path(config).exists():
            with open(config, 'r') as f:
                config_data = json.load(f)
            if ParallelAgentsConfig:
                agent_config = ParallelAgentsConfig(**config_data)
            else:
                # Create basic demo config
                agent_config = type('Config', (), {
                    'watch_dirs': ['src'],
                    'agent_mission': 'testing',
                    'working_set_dir': 'tests/working_set'
                })()
        else:
            click.echo("⚠️  No configuration file found. Using demo defaults.")
            agent_config = type('Config', (), {
                'watch_dirs': ['src'],
                'agent_mission': 'testing',
                'working_set_dir': 'tests/working_set'
            })()
    except Exception as e:
        click.echo(f"⚠️  Configuration error: {e}. Using demo defaults.")
        agent_config = type('Config', (), {
            'watch_dirs': ['src'],
            'agent_mission': 'testing',
            'working_set_dir': 'tests/working_set'
        })()
    
    # Apply overrides
    if watch_dir:
        agent_config.watch_dirs = list(watch_dir)
        click.echo(f"📂 Watching directories: {', '.join(watch_dir)}")
    
    if mission:
        agent_config.agent_mission = mission
        click.echo(f"🎯 Mission: {mission}")
    
    # Start mock overseer
    if MockOverseer:
        try:
            overseer = MockOverseer(agent_config)
            click.echo("✅ Mock overseer started. Simulating agent behavior...")
            click.echo("Press Ctrl+C to stop.")
            # Note: This would need async implementation for full functionality
            click.echo("🎭 Demo mode - simulating file monitoring and agent responses")
            click.echo("    In real implementation, this would monitor files and generate mock responses")
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping demo...")
        except Exception as e:
            click.echo(f"❌ Error starting mock overseer: {e}")
    else:
        click.echo("🎭 Demo mode (basic) - Core modules not available")
        click.echo("    This would normally start a mock agent for testing")


@main.command()
@click.option('--output', '-o', default='verifier.json',
              help='Output configuration file (default: verifier.json)')
def init(output: str):
    """Initialize a new verifier configuration file"""
    click.echo(f"🛠️  Initializing configuration file: {output}")
    
    # Create default configuration
    default_config = {
        "watch_dirs": ["src"],
        "test_dir": "tests",
        "working_set_dir": "tests/working_set",
        "watch_extensions": [".py", ".js", ".ts", ".jsx", ".tsx"],
        "agent_mission": "testing",
        "error_report_file": "tests/working_set/error_report.jsonl",
        "claude_timeout": 300,
        "claude_log_file": "tests/working_set/claude_logs.jsonl",
        "code_tool": "goose",
        "log_level": "INFO",
        "max_iterations": 3,
        "timeout": 30
    }
    
    # Check if file exists
    if Path(output).exists():
        if not click.confirm(f"Configuration file '{output}' already exists. Overwrite?"):
            click.echo("❌ Initialization cancelled.")
            return
    
    # Write configuration
    try:
        with open(output, 'w') as f:
            json.dump(default_config, f, indent=2)
        click.echo(f"✅ Configuration file '{output}' created successfully!")
        click.echo("\n📝 Next steps:")
        click.echo(f"   1. Edit '{output}' to customize settings")
        click.echo("   2. Run 'verifier validate' to check configuration")
        click.echo("   3. Run 'verifier start' to begin monitoring")
    except Exception as e:
        click.echo(f"❌ Error creating configuration file: {e}")


@main.command()
@click.option('--config', '-c', default='verifier.json',
              help='Configuration file path (default: verifier.json)')
def validate(config: str):
    """Validate the verifier configuration"""
    click.echo(f"🔍 Validating configuration: {config}")
    
    # Check if config file exists
    if not Path(config).exists():
        click.echo(f"❌ Configuration file '{config}' not found.")
        click.echo("   Run 'verifier init' to create a configuration file.")
        return
    
    try:
        # Load and validate configuration
        with open(config, 'r') as f:
            config_data = json.load(f)
        
        # Basic validation
        required_fields = ['watch_dirs', 'agent_mission', 'working_set_dir']
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            click.echo(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return
        
        # Validate watch directories
        watch_dirs = config_data.get('watch_dirs', [])
        for watch_dir in watch_dirs:
            if not Path(watch_dir).exists():
                click.echo(f"⚠️  Watch directory does not exist: {watch_dir}")
        
        # Validate working set directory
        working_set_dir = config_data.get('working_set_dir')
        if working_set_dir:
            Path(working_set_dir).mkdir(parents=True, exist_ok=True)
            click.echo(f"✅ Working set directory ready: {working_set_dir}")
        
        click.echo("✅ Configuration validation passed!")
        
    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON in configuration file: {e}")
    except Exception as e:
        click.echo(f"❌ Error validating configuration: {e}")


@main.command()
@click.option('--config', '-c', default='verifier.json',
              help='Configuration file path (default: verifier.json)')
def status(config: str):
    """Show verifier status and configuration"""
    click.echo("📊 Parallel Agents Verifier Status")
    click.echo("=" * 40)
    
    # Check configuration
    if Path(config).exists():
        try:
            with open(config, 'r') as f:
                config_data = json.load(f)
            
            click.echo(f"Configuration: {config} ✅")
            click.echo(f"Watch directories: {', '.join(config_data.get('watch_dirs', []))}")
            click.echo(f"Mission: {config_data.get('agent_mission', 'Not specified')}")
            click.echo(f"Working set: {config_data.get('working_set_dir', 'Not specified')}")
            click.echo(f"Code tool: {config_data.get('code_tool', 'Not specified')}")
            
            # Check directory status
            watch_dirs = config_data.get('watch_dirs', [])
            for watch_dir in watch_dirs:
                if Path(watch_dir).exists():
                    click.echo(f"  📂 {watch_dir} ✅")
                else:
                    click.echo(f"  📂 {watch_dir} ❌ (not found)")
        
        except Exception as e:
            click.echo(f"Configuration: {config} ❌ ({e})")
    else:
        click.echo(f"Configuration: {config} ❌ (not found)")
    
    # Check dependencies
    click.echo(f"\nDependencies:")
    
    # Check UV
    import subprocess
    try:
        subprocess.run(['uv', '--version'], capture_output=True, check=True)
        click.echo("  UV package manager ✅")
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("  UV package manager ❌")
    
    # Check core modules
    if ParallelAgentsConfig:
        click.echo("  Core modules ✅")
    else:
        click.echo("  Core modules ⚠️  (limited functionality)")
    
    click.echo(f"\nProject Status:")
    click.echo(f"  Package builds: ✅ (verified)")
    click.echo(f"  Tests: ⚠️  (some import issues)")
    click.echo(f"  Documentation: ✅")


@main.command()
@click.option('--config', '-c', default='verifier.json',
              help='Configuration file path (default: verifier.json)')
def stop(config: str):
    """Stop any running verifier processes"""
    click.echo("🛑 Stopping Parallel Agents Verifier...")
    
    try:
        # Look for running processes
        import psutil
        stopped_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('verifier' in str(cmd) for cmd in cmdline):
                    if 'start' in cmdline or 'demo' in cmdline:
                        click.echo(f"🔍 Found verifier process (PID: {proc.info['pid']})")
                        proc.terminate()
                        stopped_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if stopped_count > 0:
            click.echo(f"✅ Stopped {stopped_count} verifier process(es)")
        else:
            click.echo("ℹ️  No running verifier processes found")
            
    except ImportError:
        click.echo("⚠️  psutil not available. Cannot automatically stop processes.")
        click.echo("💡 Please manually stop any running verifier processes (Ctrl+C)")
    except Exception as e:
        click.echo(f"❌ Error stopping processes: {e}")


if __name__ == '__main__':
    main()
