#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para validar que los links de documentación en README.md existen.

Verifica que todos los archivos referenciados en la sección de documentación
del README existan realmente.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Configurar encoding para Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')


def extract_doc_links_from_readme(readme_path: Path) -> List[Tuple[str, str]]:
    """Extrae los links de documentación del README."""
    links = []
    
    if not readme_path.exists():
        print(f"✗ README no encontrado: {readme_path}")
        return links
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        in_docs_section = False
        for line in f:
            # Detectar inicio de sección de documentación
            if line.strip().startswith("## Documentation"):
                in_docs_section = True
                continue
            
            # Detectar fin de sección de documentación
            if in_docs_section and line.strip().startswith("##"):
                if not line.strip().startswith("## Documentation"):
                    break
            
            # Extraer links markdown
            if in_docs_section and "[" in line and "](" in line:
                # Formato: [text](path)
                import re
                matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
                for text, path in matches:
                    # Solo procesar paths relativos que parezcan archivos de docs
                    if path.startswith("docs/") or path.startswith("./docs/"):
                        links.append((text, path))
    
    return links


def validate_doc_link(base_path: Path, link_path: str) -> Tuple[bool, str]:
    """Valida que un link de documentación exista."""
    # Normalizar el path
    if link_path.startswith("./"):
        link_path = link_path[2:]
    
    full_path = base_path / link_path
    
    if full_path.exists():
        return True, f"[OK] {link_path}"
    else:
        return False, f"[FAIL] {link_path} (no existe)"


def main() -> int:
    """Ejecuta la validación de links de documentación."""
    print("=" * 70)
    print("VALIDACIÓN DE LINKS DE DOCUMENTACIÓN")
    print("=" * 70)
    
    # Obtener el directorio raíz del proyecto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    readme_path = project_root / "README.md"
    
    if not readme_path.exists():
        print(f"[ERROR] README.md no encontrado en {project_root}")
        return 1
    
    # Extraer links
    print("\nExtrayendo links de documentación del README...")
    links = extract_doc_links_from_readme(readme_path)
    
    if not links:
        print("[WARNING] No se encontraron links de documentación en el README")
        return 0
    
    print(f"\nEncontrados {len(links)} links de documentación\n")
    
    # Validar cada link
    print("=" * 70)
    print("VALIDANDO LINKS")
    print("=" * 70)
    
    results = []
    all_valid = True
    
    for text, path in links:
        valid, message = validate_doc_link(project_root, path)
        results.append((text, path, valid, message))
        print(f"{message} - [{text}]")
        if not valid:
            all_valid = False
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    
    valid_count = sum(1 for _, _, valid, _ in results if valid)
    total_count = len(results)
    
    print(f"\nLinks válidos: {valid_count}/{total_count}")
    
    if all_valid:
        print("\n[SUCCESS] TODOS LOS LINKS SON VALIDOS")
        return 0
    else:
        print("\n[FAIL] ALGUNOS LINKS SON INVALIDOS")
        print("\nLinks inválidos:")
        for text, path, valid, message in results:
            if not valid:
                print(f"  - [{text}]({path})")
        return 1


if __name__ == "__main__":
    sys.exit(main())

