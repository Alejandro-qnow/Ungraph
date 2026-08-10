#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validación pre-build que ejecuta todas las verificaciones necesarias
antes de construir y publicar el paquete.

Este script ejecuta:
1. Validación de links de documentación
2. Smoke test de instalación (si el paquete está instalado)
3. Tests de instalación con pytest
4. Validación de configuración de publicación

Uso:
    python scripts/pre_build_validation.py
"""

import sys
import os
import subprocess
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')


def run_script(script_path: Path, description: str) -> tuple[bool, str]:
    """Ejecuta un script y retorna (success, output)."""
    if not script_path.exists():
        return False, f"Script no encontrado: {script_path}"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=script_path.parent.parent
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)


def run_pytest(test_path: Path, description: str) -> tuple[bool, str]:
    """Ejecuta pytest en un archivo de test."""
    if not test_path.exists():
        return False, f"Test no encontrado: {test_path}"
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v"],
            capture_output=True,
            text=True,
            cwd=test_path.parent.parent
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)


def main() -> int:
    """Ejecuta todas las validaciones pre-build."""
    print("=" * 70)
    print("VALIDACION PRE-BUILD - UNGRAPH")
    print("=" * 70)
    
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / "scripts"
    tests_dir = project_root / "tests"
    
    results = []
    
    # 1. Validar links de documentación
    print("\n" + "=" * 70)
    print("1. VALIDACION DE LINKS DE DOCUMENTACION")
    print("=" * 70)
    doc_links_script = scripts_dir / "validate_docs_links.py"
    success, output = run_script(doc_links_script, "Validación de links")
    results.append(("Links de documentación", success))
    print(output)
    
    # 2. Tests de instalación (pytest)
    print("\n" + "=" * 70)
    print("2. TESTS DE INSTALACION (pytest)")
    print("=" * 70)
    installation_test = tests_dir / "test_installation.py"
    success, output = run_pytest(installation_test, "Tests de instalación")
    results.append(("Tests de instalación", success))
    if success:
        # Mostrar solo resumen si pasa
        lines = output.split('\n')
        summary_lines = [l for l in lines if 'passed' in l.lower() or 'failed' in l.lower()]
        print('\n'.join(summary_lines))
    else:
        print(output)
    
    # 3. Smoke test (solo si el paquete está instalado)
    print("\n" + "=" * 70)
    print("3. SMOKE TEST DE INSTALACION")
    print("=" * 70)
    try:
        import ungraph
        smoke_test_script = scripts_dir / "smoke_test_installation.py"
        success, output = run_script(smoke_test_script, "Smoke test")
        results.append(("Smoke test", success))
        print(output)
    except ImportError:
        print("[SKIP] Paquete no instalado - smoke test omitido")
        print("[INFO] Para ejecutar smoke test: uv pip install -e .")
        results.append(("Smoke test", None))  # None = skipped
    
    # 4. Validación de configuración de publicación
    print("\n" + "=" * 70)
    print("4. VALIDACION DE CONFIGURACION DE PUBLICACION")
    print("=" * 70)
    publish_script = scripts_dir / "publish.py"
    if publish_script.exists():
        # Ejecutar validate sin --test para verificar configuración de producción
        try:
            result = subprocess.run(
                [sys.executable, str(publish_script), "validate"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            success = result.returncode == 0
            results.append(("Configuración de publicación", success))
            print(result.stdout)
            if not success:
                print(result.stderr)
        except Exception as e:
            print(f"[ERROR] Error al validar configuración: {e}")
            results.append(("Configuración de publicación", False))
    else:
        print("[SKIP] Script de publicación no encontrado")
        results.append(("Configuración de publicación", None))
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success is True)
    failed = sum(1 for _, success in results if success is False)
    skipped = sum(1 for _, success in results if success is None)
    total = len(results)
    
    print(f"\nTotal de validaciones: {total}")
    print(f"  [PASS] Pasaron: {passed}")
    print(f"  [FAIL] Fallaron: {failed}")
    print(f"  [SKIP] Omitidas: {skipped}")
    
    print("\nDetalle:")
    for name, success in results:
        if success is True:
            status = "[PASS]"
        elif success is False:
            status = "[FAIL]"
        else:
            status = "[SKIP]"
        print(f"  {status} {name}")
    
    if failed == 0:
        print("\n[SUCCESS] TODAS LAS VALIDACIONES PASARON")
        print("\nEl paquete esta listo para build y publicacion.")
        print("\nProximos pasos:")
        print("  1. python scripts/publish.py build")
        print("  2. python scripts/publish.py validate --test")
        print("  3. python scripts/publish.py publish --test")
        return 0
    else:
        print("\n[FAIL] ALGUNAS VALIDACIONES FALLARON")
        print("\nRevisar los errores arriba antes de construir el paquete.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


