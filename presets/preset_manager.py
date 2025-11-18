"""Preset Manager - Load and save workflows"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class OperationConfig:
    """Configuration for a single operation in a preset"""
    operation_id: str
    parameters: Dict
    order: int
    enabled: bool = True
    
    def to_dict(self):
        return asdict(self)

@dataclass  
class Preset:
    """A saved workflow preset"""
    id: str
    name: str
    description: str
    category: str
    operations: List[OperationConfig]
    created_at: str
    updated_at: str
    author: str = "user"
    usage_count: int = 0
    is_system: bool = False
    
    def to_dict(self):
        return {
            **asdict(self),
            'operations': [op.to_dict() if hasattr(op, 'to_dict') else op for op in self.operations]
        }

class PresetManager:
    """Manage loading and saving presets"""
    
    def __init__(self, presets_dir: Path = None):
        if presets_dir is None:
            presets_dir = Path(__file__).parent
        self.presets_dir = presets_dir
        self.system_dir = presets_dir / "system"
        self.user_dir = presets_dir / "user"
        
        # Ensure directories exist
        self.system_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)
    
    def load_preset(self, preset_id: str) -> Optional[Preset]:
        """Load a preset by ID"""
        # Try system presets first
        system_file = self.system_dir / f"{preset_id}.json"
        if system_file.exists():
            return self._load_preset_file(system_file, is_system=True)
        
        # Try user presets
        user_file = self.user_dir / f"{preset_id}.json"
        if user_file.exists():
            return self._load_preset_file(user_file, is_system=False)
        
        return None
    
    def _load_preset_file(self, filepath: Path, is_system: bool) -> Preset:
        """Load preset from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Convert operations to OperationConfig objects
        operations = [
            OperationConfig(**op) if isinstance(op, dict) else op
            for op in data.get('operations', [])
        ]
        
        return Preset(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            category=data['category'],
            operations=operations,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            author=data.get('author', 'user'),
            usage_count=data.get('usage_count', 0),
            is_system=is_system
        )
    
    def save_preset(self, preset: Preset):
        """Save a preset"""
        if preset.is_system:
            raise ValueError("Cannot modify system presets")
        
        preset.updated_at = datetime.now().isoformat()
        
        filepath = self.user_dir / f"{preset.id}.json"
        with open(filepath, 'w') as f:
            json.dump(preset.to_dict(), f, indent=2)
    
    def list_presets(self, category: str = None) -> List[Preset]:
        """List all available presets"""
        presets = []
        
        # Load system presets
        for file in self.system_dir.glob("*.json"):
            try:
                preset = self._load_preset_file(file, is_system=True)
                if category is None or preset.category == category:
                    presets.append(preset)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        
        # Load user presets  
        for file in self.user_dir.glob("*.json"):
            try:
                preset = self._load_preset_file(file, is_system=False)
                if category is None or preset.category == category:
                    presets.append(preset)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        
        return presets
    
    def delete_preset(self, preset_id: str):
        """Delete a user preset"""
        filepath = self.user_dir / f"{preset_id}.json"
        if filepath.exists():
            filepath.unlink()
        else:
            raise ValueError(f"Preset {preset_id} not found")
