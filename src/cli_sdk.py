"""
SDK-based CLI - New CLI implementation using the SDK as backend
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import SDK functions
try:
    from .sdk_api import *
    from .sdk_config import create_config_from_profile, get_available_profiles
except ImportError:
    from sdk_api import *
    from sdk_config import create_config_from_profile, get_available_profiles


@click.group()
@click.option('--config', '-c', default='verifier.json', help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """Parallel Agents CLI - SDK Edition"""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config


@cli.command()
@click.option('--output', '-o', default='verifier.json', help='Output configuration file')
@click.option('--profile', '-p', help='Configuration profile to use')
@click.option('--overwrite', is_flag=True, help='Overwrite existing configuration')
@click.pass_context
def init(ctx, output, profile, overwrite):
    """Initialize a new configuration file"""
    config_file = output
    
    try:
        if profile:
            # Use profile
            config = create_config_from_profile(profile, config_file)
            click.echo(f"✅ Created configuration from profile '{profile}': {config_file}")
        else:
            # Use default
            result = init_config(config_file, overwrite)
            if result["success"]:
                click.echo(f"✅ {result['message']}")
            else:
                click.echo(f"❌ {result['error']}", err=True)
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"❌ Failed to initialize configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def profiles(ctx):
    """List available configuration profiles"""
    try:
        profiles = get_available_profiles()
        
        click.echo("📋 Available Configuration Profiles:")
        click.echo("=" * 40)
        
        for profile_name, profile_info in profiles.items():
            click.echo(f"\n🔧 {profile_name}")
            click.echo(f"   {profile_info['description']}")
            click.echo(f"   Code Tool: {profile_info['config_overrides'].get('code_tool', 'default')}")
            click.echo(f"   Mission: {profile_info['config_overrides'].get('agent_mission', 'default')}")
            
    except Exception as e:
        click.echo(f"❌ Failed to get profiles: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate the configuration"""
    config_file = ctx.obj['config_file']
    
    try:
        result = validate_config(config_file)
        
        if result["success"]:
            click.echo(f"🔍 Validating configuration: {config_file}")
            
            if result["valid"]:
                click.echo("✅ Configuration is valid!")
            else:
                click.echo("❌ Configuration has errors:")
                for error in result["errors"]:
                    click.echo(f"  • {error}")
                    
            if result["warnings"]:
                click.echo("\n⚠️  Warnings:")
                for warning in result["warnings"]:
                    click.echo(f"  • {warning}")
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration"""
    config_file = ctx.obj['config_file']
    
    try:
        result = get_config(config_file)
        
        if result["success"]:
            click.echo(f"📊 Configuration: {config_file}")
            click.echo("=" * 40)
            click.echo(json.dumps(result["config"], indent=2))
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to get configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--mission', '-m', help='Agent mission (overrides config)')
@click.option('--demo', is_flag=True, help='Start in demo mode')
@click.option('--agent-id', help='Custom agent identifier')
@click.pass_context
def start(ctx, mission, demo, agent_id):
    """Start a new agent session"""
    config_file = ctx.obj['config_file']
    
    try:
        click.echo("🚀 Starting agent...")
        
        result = start_agent(
            mission=mission,
            demo_mode=demo,
            agent_id=agent_id,
            config_file=config_file
        )
        
        if result["success"]:
            click.echo(f"✅ {result['message']}")
            click.echo(f"📋 Agent ID: {result['agent_id']}")
            click.echo(f"🎯 Mission: {result['mission']}")
            click.echo(f"🔧 Mode: {result['mode']}")
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to start agent: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('agent_id')
@click.pass_context
def stop(ctx, agent_id):
    """Stop a specific agent session"""
    config_file = ctx.obj['config_file']
    
    try:
        result = stop_agent(agent_id, config_file)
        
        if result["success"]:
            click.echo(f"✅ {result['message']}")
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to stop agent: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def stop_all(ctx):
    """Stop all running agent sessions"""
    config_file = ctx.obj['config_file']
    
    try:
        result = stop_all_agents(config_file)
        
        if result["success"]:
            click.echo(f"✅ {result['message']}")
            click.echo(f"🛑 Stopped agents: {', '.join(result['stopped_agents'])}")
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to stop agents: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--all', 'show_all', is_flag=True, help='Show stopped agents too')
@click.pass_context
def agents(ctx, show_all):
    """List agent sessions"""
    config_file = ctx.obj['config_file']
    
    try:
        result = get_agents(include_stopped=show_all, config_file=config_file)
        
        if result["success"]:
            click.echo("🤖 Agent Sessions:")
            click.echo("=" * 40)
            
            if not result["agents"]:
                click.echo("📭 No agents found")
                return
                
            for agent_id, agent_info in result["agents"].items():
                status_emoji = {
                    'running': '🟢',
                    'starting': '🟡',
                    'stopped': '🔴',
                    'failed': '❌'
                }.get(agent_info['status'], '⚪')
                
                click.echo(f"\n{status_emoji} {agent_id}")
                click.echo(f"   Mission: {agent_info['mission']}")
                click.echo(f"   Status: {agent_info['status']}")
                click.echo(f"   Mode: {agent_info['mode']}")
                click.echo(f"   Started: {agent_info['started_at']}")
                
                if agent_info.get('stopped_at'):
                    click.echo(f"   Stopped: {agent_info['stopped_at']}")
                    
            click.echo(f"\n📊 Summary: {result['running']} running, {result['stopped']} stopped")
            
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to get agents: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('agent_id')
@click.pass_context
def status(ctx, agent_id):
    """Show detailed status for a specific agent"""
    config_file = ctx.obj['config_file']
    
    try:
        result = get_agent_status(agent_id, config_file)
        
        if result["success"]:
            click.echo(f"📊 Agent Status: {agent_id}")
            click.echo("=" * 40)
            
            status_emoji = {
                'running': '🟢',
                'starting': '🟡',
                'stopped': '🔴',
                'failed': '❌'
            }.get(result['status'], '⚪')
            
            click.echo(f"Status: {status_emoji} {result['status']}")
            click.echo(f"Mission: {result['mission']}")
            click.echo(f"Mode: {result['mode']}")
            click.echo(f"Started: {result['started_at']}")
            
            if result.get('stopped_at'):
                click.echo(f"Stopped: {result['stopped_at']}")
                
            if result.get('log_file'):
                click.echo(f"Log File: {result['log_file']}")
                click.echo(f"Log Exists: {'✅' if result.get('log_exists') else '❌'}")
                
                if result.get('log_size'):
                    click.echo(f"Log Size: {result['log_size']} bytes")
                    
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to get agent status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--detailed', is_flag=True, help='Show detailed information')
@click.pass_context
def changes(ctx, detailed):
    """List changes in working set"""
    config_file = ctx.obj['config_file']
    
    try:
        result = get_working_set_changes(config_file)
        
        if result["success"]:
            click.echo("📂 Working Set Changes:")
            click.echo("=" * 40)
            
            if result["total_files"] == 0:
                click.echo("📭 No files in working set")
                return
                
            click.echo(f"Total Files: {result['total_files']}")
            
            if detailed:
                click.echo("\n📄 Files by Type:")
                for file_type, files in result["by_type"].items():
                    click.echo(f"\n🔸 {file_type.upper()} ({len(files)} files):")
                    for file_info in files:
                        click.echo(f"  • {file_info['path']} ({file_info['size']} bytes)")
            else:
                click.echo("\n📊 File Types:")
                for file_type, files in result["by_type"].items():
                    click.echo(f"  • {file_type}: {len(files)} files")
                    
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to get working set changes: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('source_path')
@click.option('--dest', help='Destination path')
@click.option('--preview', is_flag=True, help='Preview the operation')
@click.pass_context
def elevate(ctx, source_path, dest, preview):
    """Elevate a file from working set to main codebase"""
    config_file = ctx.obj['config_file']
    
    try:
        result = elevate_file(
            source_path=source_path,
            dest_path=dest,
            preview=preview,
            config_file=config_file
        )
        
        if result["success"]:
            if preview:
                click.echo("👀 Preview Mode:")
                click.echo(f"Source: {result['source']}")
                click.echo(f"Destination: {result['destination']}")
                click.echo(f"Would overwrite: {'Yes' if result['would_overwrite'] else 'No'}")
                
                if result.get('content_preview'):
                    click.echo("\n📄 Content Preview:")
                    click.echo(result['content_preview'])
            else:
                if result.get('success', True):
                    click.echo(f"✅ {result.get('message', 'File elevated successfully')}")
                else:
                    click.echo(f"❌ {result.get('error', 'Elevation failed')}")
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to elevate file: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--src-dir', default='src', help='Source directory to review')
@click.pass_context
def review(ctx, src_dir):
    """Run code review and generate suggestions"""
    config_file = ctx.obj['config_file']
    
    try:
        click.echo(f"🔍 Running code review on: {src_dir}")
        
        result = run_code_review(src_dir, config_file)
        
        if result["success"]:
            click.echo(f"✅ Code review completed")
            click.echo(f"📋 Generated {result['total']} suggestions")
            
            if result.get('by_type'):
                click.echo("\n📊 Suggestions by Type:")
                for suggestion_type, count in result['by_type'].items():
                    click.echo(f"  • {suggestion_type}: {count}")
                    
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Code review failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--filter-type', help='Filter suggestions by type')
@click.option('--preview', is_flag=True, help='Preview what would be applied')
@click.pass_context
def apply_suggestions(ctx, filter_type, preview):
    """Apply code review suggestions"""
    config_file = ctx.obj['config_file']
    
    try:
        result = apply_suggestions(
            filter_type=filter_type,
            preview=preview,
            config_file=config_file
        )
        
        if result["success"]:
            if preview:
                click.echo("👀 Preview Mode:")
                click.echo(f"Would apply {result['total']} suggestions")
                
                if filter_type:
                    click.echo(f"Filtered by type: {filter_type}")
                    
            else:
                click.echo(f"✅ Applied {result.get('applied', 0)} suggestions")
                
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to apply suggestions: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--agent-id', help='Show logs for specific agent')
@click.option('--limit', default=10, help='Number of log entries to show')
@click.pass_context
def logs(ctx, agent_id, limit):
    """Show recent log entries"""
    config_file = ctx.obj['config_file']
    
    try:
        result = get_logs(
            agent_id=agent_id,
            limit=limit,
            config_file=config_file
        )
        
        if result["success"]:
            click.echo(f"📝 Recent Logs ({result['count']} entries):")
            click.echo("=" * 40)
            
            if not result["logs"]:
                click.echo("📭 No log entries found")
                return
                
            for log_entry in result["logs"]:
                timestamp = log_entry.get('timestamp', 'Unknown')
                message = log_entry.get('message', '')
                level = log_entry.get('level', 'info')
                
                level_emoji = {
                    'error': '❌',
                    'warning': '⚠️',
                    'info': 'ℹ️',
                    'debug': '🐛'
                }.get(level, 'ℹ️')
                
                click.echo(f"{level_emoji} [{timestamp}] {message}")
                
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to get logs: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def system_status(ctx):
    """Show comprehensive system status"""
    config_file = ctx.obj['config_file']
    
    try:
        result = get_system_status(config_file)
        
        if result["success"]:
            click.echo("🖥️  System Status:")
            click.echo("=" * 40)
            
            # Configuration status
            config_result = result["config"]
            if config_result["success"]:
                click.echo("✅ Configuration: Loaded")
            else:
                click.echo(f"❌ Configuration: {config_result['error']}")
                
            # Validation status
            validation_result = result["validation"]
            if validation_result["success"]:
                if validation_result["valid"]:
                    click.echo("✅ Validation: Passed")
                else:
                    click.echo(f"❌ Validation: Failed ({len(validation_result['errors'])} errors)")
            else:
                click.echo(f"❌ Validation: {validation_result['error']}")
                
            # Agents status
            agents_result = result["agents"]
            if agents_result["success"]:
                click.echo(f"🤖 Agents: {agents_result['running']}/{agents_result['total']} running")
            else:
                click.echo(f"❌ Agents: {agents_result['error']}")
                
            # Working set status
            ws_result = result["working_set"]
            if ws_result["success"]:
                click.echo(f"📂 Working Set: {ws_result['total_files']} files")
            else:
                click.echo(f"❌ Working Set: {ws_result['error']}")
                
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to get system status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Perform system health check"""
    config_file = ctx.obj['config_file']
    
    try:
        result = health_check(config_file)
        
        if result["success"]:
            health_info = result["health"]
            
            click.echo("🏥 System Health Check:")
            click.echo("=" * 40)
            
            # Overall health
            if health_info["healthy"]:
                click.echo("✅ Overall Health: HEALTHY")
            else:
                click.echo("❌ Overall Health: UNHEALTHY")
                
            click.echo("\n📋 Components:")
            
            # Individual components
            components = [
                ("Configuration Loaded", health_info["config_loaded"]),
                ("Configuration Valid", health_info["config_valid"]),
                ("Working Set Accessible", health_info["working_set_accessible"]),
                ("Code Tool Available", health_info["code_tool_available"])
            ]
            
            for component, status in components:
                status_icon = "✅" if status else "❌"
                click.echo(f"  {status_icon} {component}")
                
            # Running agents
            click.echo(f"  🤖 Running Agents: {health_info['agents_running']}")
            
            # Errors and warnings
            if health_info.get("config_errors"):
                click.echo("\n❌ Configuration Errors:")
                for error in health_info["config_errors"]:
                    click.echo(f"  • {error}")
                    
            if health_info.get("config_warnings"):
                click.echo("\n⚠️  Configuration Warnings:")
                for warning in health_info["config_warnings"]:
                    click.echo(f"  • {warning}")
                    
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def cleanup(ctx):
    """Clean up all resources and stop all agents"""
    try:
        result = cleanup()
        
        if result["success"]:
            click.echo(f"✅ {result['message']}")
        else:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 