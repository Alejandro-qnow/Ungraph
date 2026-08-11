#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smoke test para validar instalación e imports básicos del paquete.

Este script valida que:
1. El paquete se puede importar correctamente
2. Todas las funciones públicas del API están disponibles
3. Los imports internos funcionan correctamente
4. La configuración básica funciona

Uso:
    python scripts/smoke_test_installation.py

O después de instalar:
    pip install .
    python scripts/smoke_test_installation.py
"""

import sys
import os
import importlib
from pathlib import Path
from typing import List, Tuple

# Configurar encoding para Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')


def test_import(module_name: str, description: str) -> Tuple[bool, str]:
    """Intenta importar un módulo y retorna (success, message)."""
    try:
        importlib.import_module(module_name)
        return True, f"[OK] {description}: {module_name}"
    except ImportError as e:
        return False, f"[FAIL] {description}: {module_name} - {e}"
    except Exception as e:
        return False, f"[FAIL] {description}: {module_name} - {type(e).__name__}: {e}"


def test_critical_packaging() -> Tuple[bool, List[str]]:
    """Test crítico de packaging: valida que el import básico funciona."""
    print("\n" + "=" * 70)
    print("TEST CRÍTICO DE PACKAGING")
    print("=" * 70)
    
    messages = []
    
    # Test 1: Import básico del paquete
    try:
        import ungraph
        messages.append("[OK] import ungraph funciona")
    except ImportError as e:
        messages.append(f"[FAIL] import ungraph falló: {e}")
        return False, messages
    except Exception as e:
        messages.append(f"[FAIL] Error inesperado al importar ungraph: {e}")
        return False, messages
    
    # Test 2: Verificar que configure está disponible (test crítico mencionado por el usuario)
    try:
        if hasattr(ungraph, 'configure'):
            if callable(ungraph.configure):
                messages.append("[OK] ungraph.configure es callable")
            else:
                messages.append("[FAIL] ungraph.configure existe pero no es callable")
                return False, messages
        else:
            messages.append("[FAIL] ungraph.configure no existe")
            return False, messages
    except Exception as e:
        messages.append(f"[FAIL] Error al verificar ungraph.configure: {e}")
        return False, messages
    
    # Test 3: Verificar que el módulo core se puede importar
    try:
        from ungraph.core import configure as core_configure
        messages.append("[OK] ungraph.core se puede importar")
    except ImportError as e:
        messages.append(f"[FAIL] No se puede importar ungraph.core: {e}")
        return False, messages
    
    for msg in messages:
        print(msg)
    
    return True, messages

def test_public_api() -> Tuple[bool, List[str]]:
    """Valida que todas las funciones públicas del API estén disponibles."""
    print("\n" + "=" * 70)
    print("VALIDACIÓN DE API PÚBLICO")
    print("=" * 70)
    
    try:
        import ungraph
    except ImportError as e:
        return False, [f"[FAIL] No se puede importar ungraph: {e}"]
    
    messages = []
    all_passed = True
    
    # Verificar funciones de configuración
    config_functions = [
        ("configure", "Función de configuración"),
        ("reset_configuration", "Función de reset de configuración"),
    ]
    
    for func_name, desc in config_functions:
        if hasattr(ungraph, func_name):
            if callable(getattr(ungraph, func_name)):
                messages.append(f"[OK] {desc}: ungraph.{func_name}()")
            else:
                messages.append(f"[FAIL] {desc}: ungraph.{func_name} no es callable")
                all_passed = False
        else:
            messages.append(f"[FAIL] {desc}: ungraph.{func_name} no existe")
            all_passed = False
    
    # Verificar funciones principales
    main_functions = [
        ("ingest_document", "Función de ingestión de documentos"),
        ("search", "Función de búsqueda básica"),
        ("vector_search", "Función de búsqueda vectorial"),
        ("hybrid_search", "Función de búsqueda híbrida"),
        ("search_with_pattern", "Función de búsqueda con patrones"),
        ("suggest_chunking_strategy", "Función de sugerencia de chunking"),
    ]
    
    for func_name, desc in main_functions:
        if hasattr(ungraph, func_name):
            if callable(getattr(ungraph, func_name)):
                messages.append(f"[OK] {desc}: ungraph.{func_name}()")
            else:
                messages.append(f"[FAIL] {desc}: ungraph.{func_name} no es callable")
                all_passed = False
        else:
            messages.append(f"[FAIL] {desc}: ungraph.{func_name} no existe")
            all_passed = False
    
    # Verificar clases públicas
    public_classes = [
        ("Chunk", "Clase Chunk"),
        ("SearchResult", "Clase SearchResult"),
        ("ChunkingRecommendation", "Clase ChunkingRecommendation"),
        ("GraphPattern", "Clase GraphPattern"),
    ]
    
    for class_name, desc in public_classes:
        if hasattr(ungraph, class_name):
            messages.append(f"[OK] {desc}: ungraph.{class_name}")
        else:
            messages.append(f"[FAIL] {desc}: ungraph.{class_name} no existe")
            all_passed = False
    
    # Verificar versión
    if hasattr(ungraph, "__version__"):
        messages.append(f"[OK] Version: {ungraph.__version__}")
    else:
        messages.append("[FAIL] __version__ no esta definido")
        all_passed = False
    
    for msg in messages:
        print(msg)
    
    return all_passed, messages


def test_internal_imports() -> Tuple[bool, List[str]]:
    """Valida que los imports internos funcionen correctamente."""
    print("\n" + "=" * 70)
    print("VALIDACIÓN DE IMPORTS INTERNOS")
    print("=" * 70)
    
    imports_to_test = [
        ("ungraph.core.configuration", "Módulo de configuración"),
        ("ungraph.domain.entities.chunk", "Entidad Chunk"),
        ("ungraph.domain.services.search_service", "Servicio de búsqueda"),
        ("ungraph.application.use_cases.ingest_document", "Caso de uso de ingestión"),
        ("ungraph.infrastructure.services.neo4j_search_service", "Servicio de búsqueda Neo4j"),
    ]
    
    results = []
    all_passed = True
    
    for module_name, description in imports_to_test:
        success, message = test_import(module_name, description)
        results.append(message)
        if not success:
            all_passed = False
        print(message)
    
    return all_passed, results


def test_basic_functionality() -> Tuple[bool, List[str]]:
    """Valida funcionalidad básica sin requerir Neo4j."""
    print("\n" + "=" * 70)
    print("VALIDACIÓN DE FUNCIONALIDAD BÁSICA")
    print("=" * 70)
    
    messages = []
    all_passed = True
    
    try:
        import ungraph
        
        # Test 1: Configuración básica (sin conexión real)
        try:
            # Solo verificar que la función existe y acepta parámetros
            if hasattr(ungraph, 'configure') and callable(ungraph.configure):
                messages.append("[OK] Funcion configure() disponible")
            else:
                messages.append("[FAIL] Funcion configure() no disponible")
                all_passed = False
        except Exception as e:
            messages.append(f"[FAIL] Error al verificar configure(): {e}")
            all_passed = False
        
        # Test 2: Verificar que get_settings funciona
        try:
            from ungraph.core.configuration import get_settings
            settings = get_settings()
            messages.append(f"[OK] get_settings() funciona - Database: {settings.neo4j_database}")
        except Exception as e:
            messages.append(f"[FAIL] Error en get_settings(): {e}")
            all_passed = False
        
        # Test 3: Verificar que las clases se pueden instanciar (sin ejecutar)
        try:
            from ungraph.domain.services.search_service import SearchResult
            # Solo verificar que la clase existe, no instanciarla
            messages.append("[OK] SearchResult importable")
        except Exception as e:
            messages.append(f"[FAIL] Error al importar SearchResult: {e}")
            all_passed = False
        
    except Exception as e:
        messages.append(f"✗ Error crítico: {e}")
        all_passed = False
    
    for msg in messages:
        print(msg)
    
    return all_passed, messages


def main() -> int:
    """Ejecuta todos los smoke tests."""
    print("=" * 70)
    print("SMOKE TEST DE INSTALACION - UNGRAPH")
    print("=" * 70)
    print(f"\nPython version: {sys.version.split()[0]}")
    print(f"Python path: {sys.executable}")
    
    # Verificar si el paquete está instalado
    try:
        import ungraph
        print(f"\n[INFO] Paquete ungraph encontrado (version: {getattr(ungraph, '__version__', 'unknown')})")
    except ImportError:
        print("\n[WARNING] Paquete ungraph no encontrado.")
        print("[INFO] Este script debe ejecutarse DESPUES de instalar el paquete.")
        print("[INFO] En CI/CD, el paquete se instala automaticamente antes de ejecutar este script.")
        print("\nPara probar localmente:")
        print("  Opcion 1 (desarrollo):")
        print("    1. uv pip install -e .")
        print("    2. python scripts/smoke_test_installation.py")
        print("\n  Opcion 2 (desde wheel):")
        print("    1. uv build")
        print("    2. uv pip install dist/ungraph-*.whl")
        print("    3. python scripts/smoke_test_installation.py")
        return 1
    
    # Ejecutar tests (empezar con el test crítico de packaging)
    packaging_passed, packaging_messages = test_critical_packaging()
    api_passed, api_messages = test_public_api()
    imports_passed, import_messages = test_internal_imports()
    functionality_passed, func_messages = test_basic_functionality()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    
    total_tests = 4
    passed_tests = sum([packaging_passed, api_passed, imports_passed, functionality_passed])
    
    print(f"\nPackaging Critico: {'[PASS]' if packaging_passed else '[FAIL]'}")
    print(f"API Publico: {'[PASS]' if api_passed else '[FAIL]'}")
    print(f"Imports Internos: {'[PASS]' if imports_passed else '[FAIL]'}")
    print(f"Funcionalidad Basica: {'[PASS]' if functionality_passed else '[FAIL]'}")
    
    print(f"\nResultado: {passed_tests}/{total_tests} tests pasaron")
    
    if passed_tests == total_tests:
        print("\n[SUCCESS] TODOS LOS TESTS PASARON - El paquete esta correctamente instalado")
        return 0
    else:
        print("\n[FAIL] ALGUNOS TESTS FALLARON - Revisar errores arriba")
        return 1


if __name__ == "__main__":
    sys.exit(main())

