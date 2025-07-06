"""
Configuration management API routes
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.config.models import VerifierConfig
from ...core.config.profiles import ConfigProfileManager


router = APIRouter()


class ConfigRequest(BaseModel):
    """Request model for configuration operations"""
    config: Dict[str, Any]


class ProfileRequest(BaseModel):
    """Request model for profile operations"""
    profile_name: str
    config_overrides: Optional[Dict[str, Any]] = None


@router.post("/validate", response_model=Dict[str, Any])
async def validate_config(request: ConfigRequest):
    """Validate a configuration"""
    try:
        # Try to create config from provided data
        config = VerifierConfig(**request.config)
        
        return {
            "success": True,
            "valid": True,
            "message": "Configuration is valid",
            "config": config.model_dump()
        }
        
    except Exception as e:
        return {
            "success": True,
            "valid": False,
            "message": f"Configuration validation failed: {str(e)}",
            "errors": [str(e)]
        }


@router.get("/profiles", response_model=Dict[str, Any])
async def get_profiles():
    """Get all available configuration profiles"""
    try:
        profiles = ConfigProfileManager.get_available_profiles()
        
        return {
            "success": True,
            "profiles": profiles,
            "total": len(profiles)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{profile_name}", response_model=Dict[str, Any])
async def create_config_from_profile(profile_name: str, overrides: Optional[Dict[str, Any]] = None):
    """Create a configuration from a profile"""
    try:
        # Get profile info
        profile_info = ConfigProfileManager.get_profile_info(profile_name)
        
        # Create base config
        config = VerifierConfig()
        
        # Apply profile overrides
        for key, value in profile_info["config_overrides"].items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Apply additional overrides if provided
        if overrides:
            for key, value in overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        return {
            "success": True,
            "message": f"Configuration created from profile '{profile_name}'",
            "profile": profile_name,
            "config": config.model_dump()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_name}", response_model=Dict[str, Any])
async def get_profile_info(profile_name: str):
    """Get information about a specific profile"""
    try:
        profile_info = ConfigProfileManager.get_profile_info(profile_name)
        
        return {
            "success": True,
            "profile_name": profile_name,
            "profile": profile_info
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=Dict[str, Any])
async def compare_configs(config1: Dict[str, Any], config2: Dict[str, Any]):
    """Compare two configurations"""
    try:
        # Create config objects
        cfg1 = VerifierConfig(**config1)
        cfg2 = VerifierConfig(**config2)
        
        # Compare configs
        diff = ConfigProfileManager.compare_configs(cfg1, cfg2)
        
        return {
            "success": True,
            "differences": diff,
            "total_differences": len(diff)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 