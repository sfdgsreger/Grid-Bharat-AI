#!/usr/bin/env python3
"""
Docker Configuration Validation Script
Validates YAML syntax and configuration completeness
"""

import yaml
import os
import sys
from pathlib import Path

def validate_yaml_file(file_path):
    """Validate YAML file syntax."""
    try:
        with open(file_path, 'r') as file:
            yaml.safe_load(file)
        print(f"✅ {file_path}: Valid YAML syntax")
        return True
    except yaml.YAMLError as e:
        print(f"❌ {file_path}: Invalid YAML syntax - {e}")
        return False
    except FileNotFoundError:
        print(f"❌ {file_path}: File not found")
        return False

def validate_dockerfile(file_path):
    """Basic Dockerfile validation."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        required_instructions = ['FROM', 'WORKDIR', 'EXPOSE']
        missing = []
        
        for instruction in required_instructions:
            if instruction not in content:
                missing.append(instruction)
        
        if missing:
            print(f"❌ {file_path}: Missing instructions - {', '.join(missing)}")
            return False
        else:
            print(f"✅ {file_path}: Valid Dockerfile structure")
            return True
            
    except FileNotFoundError:
        print(f"❌ {file_path}: File not found")
        return False

def validate_env_example():
    """Validate .env.example file."""
    try:
        with open('.env.example', 'r') as file:
            content = file.read()
        
        required_vars = ['OPENAI_API_KEY', 'LOG_LEVEL', 'VITE_API_URL']
        missing = []
        
        for var in required_vars:
            if var not in content:
                missing.append(var)
        
        if missing:
            print(f"❌ .env.example: Missing variables - {', '.join(missing)}")
            return False
        else:
            print("✅ .env.example: Contains required environment variables")
            return True
            
    except FileNotFoundError:
        print("❌ .env.example: File not found")
        return False

def main():
    """Main validation function."""
    print("🔍 Validating Docker Configuration...")
    print("=" * 50)
    
    all_valid = True
    
    # Validate YAML files
    yaml_files = [
        'docker-compose.yml',
        'docker-compose.dev.yml'
    ]
    
    for yaml_file in yaml_files:
        if not validate_yaml_file(yaml_file):
            all_valid = False
    
    # Validate Dockerfiles
    dockerfiles = [
        'backend/Dockerfile',
        'frontend/Dockerfile'
    ]
    
    for dockerfile in dockerfiles:
        if not validate_dockerfile(dockerfile):
            all_valid = False
    
    # Validate environment configuration
    if not validate_env_example():
        all_valid = False
    
    # Check for required directories
    required_dirs = ['scripts', 'nginx']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/: Directory exists")
        else:
            print(f"❌ {dir_name}/: Directory missing")
            all_valid = False
    
    # Check for deployment scripts
    script_files = ['scripts/deploy.sh', 'scripts/deploy.bat']
    for script_file in script_files:
        if os.path.exists(script_file):
            print(f"✅ {script_file}: Deployment script exists")
        else:
            print(f"❌ {script_file}: Deployment script missing")
            all_valid = False
    
    print("=" * 50)
    if all_valid:
        print("🎉 All Docker configuration files are valid!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Install Docker and Docker Compose")
        print("3. Run: ./scripts/deploy.sh dev (Linux/macOS) or scripts\\deploy.bat dev (Windows)")
        return 0
    else:
        print("❌ Some configuration files have issues. Please fix them before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())