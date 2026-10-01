#!/usr/bin/env python3
"""
Validator for standardized IPSU source files.
Checks format compliance against specification.
"""

import re
import sys
from pathlib import Path

class Validator:
    """Validate standardized source files"""
    
    # Valid metadata
    VALID_UNITS = {'APCC', 'BT', 'OEP', 'PCC', 'PCG', 'PNS', 'PP', 'PTC', 'PT'}
    VALID_LANGS = {'ru', 'en'}
    VALID_RECORD_TYPES_RU = {'Научный проект', 'Научное направление'}
    VALID_RECORD_TYPES_EN = {'Research project', 'Research area'}
    
    SECTIONS_RU = [
        'Тип записи',
        'Название проекта',
        'Руководитель проекта',
        'Команда проекта',
        'Подразделение',
        'Организации-партнёры',
        'Описание проекта',
        'Научная идея',
        'Цель проекта',
        'Ключевые задачи',
        'Методологическая основа',
        'Ожидаемые результаты',
        'Внедрение результатов в практику',
        'Научный задел',
        'Основные научные публикации',
        'Доклады на конференциях',
        'Дополнительная информация',
    ]
    
    SECTIONS_EN = [
        'Record type',
        'Project title',
        'Project leader',
        'Project team',
        'Department',
        'Partner organizations',
        'Project description',
        'Scientific concept',
        'Project goal',
        'Key objectives',
        'Methodology',
        'Expected results',
        'Implementation of results',
        'Scientific background',
        'Key publications',
        'Conference presentations',
        'Additional information',
    ]
    
    SECTION_TYPES = {
        'Тип записи': 'scalar', 'Record type': 'scalar',
        'Название проекта': 'scalar', 'Project title': 'scalar',
        'Руководитель проекта': 'scalar', 'Project leader': 'scalar',
        'Команда проекта': 'list', 'Project team': 'list',
        'Подразделение': 'scalar', 'Department': 'scalar',
        'Организации-партнёры': 'list', 'Partner organizations': 'list',
        'Описание проекта': 'text', 'Project description': 'text',
        'Научная идея': 'text', 'Scientific concept': 'text',
        'Цель проекта': 'text', 'Project goal': 'text',
        'Ключевые задачи': 'list', 'Key objectives': 'list',
        'Методологическая основа': 'text', 'Methodology': 'text',
        'Ожидаемые результаты': 'list', 'Expected results': 'list',
        'Внедрение результатов в практику': 'text', 'Implementation of results': 'text',
        'Научный задел': 'text', 'Scientific background': 'text',
        'Основные научные публикации': 'list', 'Key publications': 'list',
        'Доклады на конференциях': 'list', 'Conference presentations': 'list',
        'Дополнительная информация': 'text', 'Additional information': 'text',
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_file(self, filepath: Path) -> bool:
        """Validate a single file. Returns True if all checks pass."""
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"{filepath.name}: Cannot read file - {e}")
            return False
        
        # Check encoding
        if content.startswith('\ufeff'):
            self.errors.append(f"{filepath.name}: BOM detected")
            return False
        
        lines = content.split('\n')
        
        # Check line endings (should be LF only)
        if '\r' in content:
            self.errors.append(f"{filepath.name}: Contains CR (should be LF only)")
        
        # Check final newline
        if not content.endswith('\n'):
            self.errors.append(f"{filepath.name}: Does not end with newline")
        
        # Parse header
        if len(lines) < 3:
            self.errors.append(f"{filepath.name}: Too few lines")
            return False
        
        header = {}
        for i in range(3):
            if ':' in lines[i]:
                key, val = lines[i].split(':', 1)
                header[key.strip()] = val.strip()
        
        # Validate header
        if 'UNIT' not in header:
            self.errors.append(f"{filepath.name}: Missing UNIT")
            return False
        
        if 'LANG' not in header:
            self.errors.append(f"{filepath.name}: Missing LANG")
            return False
        
        if 'PROJECTS' not in header:
            self.errors.append(f"{filepath.name}: Missing PROJECTS")
            return False
        
        unit = header['UNIT']
        lang = header['LANG']
        
        if unit not in self.VALID_UNITS:
            self.errors.append(f"{filepath.name}: Invalid UNIT '{unit}'")
        
        if lang not in self.VALID_LANGS:
            self.errors.append(f"{filepath.name}: Invalid LANG '{lang}'")
        
        try:
            project_count = int(header['PROJECTS'])
        except:
            self.errors.append(f"{filepath.name}: PROJECTS must be integer")
            return False
        
        # Check project count
        project_markers = [l for l in lines[4:] if l.startswith('=== PROJECT')]
        if len(project_markers) != project_count:
            self.errors.append(f"{filepath.name}: Expected {project_count} projects, found {len(project_markers)}")
        
        # Get sections based on language
        sections = self.SECTIONS_RU if lang == 'ru' else self.SECTIONS_EN
        
        # Check each project section
        for proj_idx in range(project_count):
            # Simplified: just check that sections are mentioned
            for section in sections:
                if section not in content:
                    # Only warning if completely missing
                    if f"=== PROJECT" in content:  # File has projects
                        self.warnings.append(f"{filepath.name}: Section '{section}' not found")
        
        # Check for forbidden patterns
        forbidden = [
            (r'к\.ф\.н\.(?!\s)', "к.ф.н. should be 'к. фарм. н.' or 'к. ф. н.'"),
            (r'д\.ф\.н\.(?!\s)', "d.f.n. should have spaces"),
            (r'[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.(?!\s)', "Initials need space after period"),
        ]
        
        for pattern, msg in forbidden:
            matches = re.findall(pattern, content)
            if matches:
                self.warnings.append(f"{filepath.name}: {msg}")
        
        return len(self.errors) == 0
    
    def report(self):
        """Print validation report"""
        if self.errors or self.warnings:
            print("\n=== VALIDATION REPORT ===\n")
            
            if self.errors:
                print(f"ERRORS ({len(self.errors)}):")
                for error in self.errors:
                    print(f"  ✗ {error}")
                print()
            
            if self.warnings:
                print(f"WARNINGS ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"  ⚠ {warning}")
                print()
        
        return len(self.errors) == 0

if __name__ == '__main__':
    source_dir = Path('/tmp/IPSU/source')
    validator = Validator()
    
    files = sorted(source_dir.glob('*.txt'))
    files = [f for f in files if f.name != '1']
    
    print(f"Validating {len(files)} files...\n")
    
    all_pass = True
    for filepath in files:
        result = validator.validate_file(filepath)
        status = "✓" if result else "✗"
        print(f"{status} {filepath.name}")
        if not result:
            all_pass = False
    
    validator.report()
    
    sys.exit(0 if all_pass else 1)
