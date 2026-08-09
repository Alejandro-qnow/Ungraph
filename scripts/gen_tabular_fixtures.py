"""
Generador determinista del corpus de fixtures tabulares para el banco de evaluación SGI.

Crea archivos de datos realistas y diversos en ``tests/fixtures/tabular/`` junto con su
*gold mapping* (rol esperado por columna). Es determinista (seed fijo) para que las
métricas sean reproducibles.

Uso:
    python scripts/gen_tabular_fixtures.py
"""

from __future__ import annotations

import random
from pathlib import Path

try:
    import pandas as pd
    import yaml
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "Este generador requiere el extra tabular: pip install 'ungraph[tabular]'"
    ) from e

SEED = 42
FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "tabular"


def _write_gold(stem: str, gold: dict) -> None:
    (FIXTURES / f"{stem}.gold.yaml").write_text(
        yaml.safe_dump(gold, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def gen_flat_employees(rng: random.Random) -> None:
    """Plano simple: una entidad por fila, columnas mixtas."""
    departments = ["Engineering", "Sales", "HR", "Finance", "Support"]
    rows = []
    for i in range(1, 61):
        rows.append(
            {
                "employee_id": i,
                "full_name": f"Employee {i:03d}",
                "email": f"emp{i:03d}@acme.com",
                "age": rng.randint(22, 63),
                "salary": round(rng.uniform(30000, 120000), 2),
                "department": rng.choice(departments),
                "is_active": rng.choice([True, False]),
                "hire_date": f"20{rng.randint(10,23):02d}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            }
        )
    pd.DataFrame(rows).to_csv(FIXTURES / "flat_employees.csv", index=False)
    _write_gold(
        "flat_employees",
        {
            "source": "flat_employees",
            "row_node_label": "Employee",
            "roles": {
                "employee_id": "node_key",
                "full_name": "attribute",
                "email": "attribute",
                "age": "attribute",
                "salary": "attribute",
                "department": "dimension",
                "is_active": "attribute",
                "hire_date": "attribute",
            },
        },
    )


def gen_orders_fk(rng: random.Random) -> None:
    """Con claves foráneas explícitas (base para bases de datos)."""
    statuses = ["paid", "pending", "cancelled"]
    regions = ["North", "South", "East", "West"]
    rows = []
    for i in range(1, 81):
        rows.append(
            {
                "order_id": i,
                "customer_id": rng.randint(1, 20),
                "product_id": rng.randint(1, 30),
                "quantity": rng.randint(1, 10),
                "unit_price": round(rng.uniform(5, 500), 2),
                "order_date": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
                "status": rng.choice(statuses),
                "region": rng.choice(regions),
            }
        )
    pd.DataFrame(rows).to_csv(FIXTURES / "orders_fk.csv", index=False)
    _write_gold(
        "orders_fk",
        {
            "source": "orders_fk",
            "row_node_label": "Order",
            "roles": {
                "order_id": "node_key",
                "customer_id": "relation_fk",
                "product_id": "relation_fk",
                "quantity": "attribute",
                "unit_price": "attribute",
                "order_date": "attribute",
                "status": "dimension",
                "region": "dimension",
            },
        },
    )


def gen_dirty_data(rng: random.Random) -> None:
    """Sucio/real: nulos, tipos mixtos, encabezados con espacios/acentos, duplicados."""
    categorias = ["Premium", "Estándar", "Básico"]
    paises = ["Colombia", "México", "España"]
    rows = []
    for i in range(1, 51):
        monto = rng.uniform(10, 1000)
        # tipos mixtos: algunos montos como texto "N/D", algunos nulos
        if i % 11 == 0:
            monto_val = None
        elif i % 13 == 0:
            monto_val = "N/D"
        else:
            monto_val = round(monto, 2)
        rows.append(
            {
                "Id Cliente": i,
                "Nombre Completo": f"Cliente {i:03d}",
                "Categoría": rng.choice(categorias),
                "Monto (USD)": monto_val,
                "Fecha Registro": f"2023-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
                "país": rng.choice(paises) if i % 7 else None,
            }
        )
    # duplicar una fila (registro duplicado real)
    rows.append(dict(rows[0]))
    pd.DataFrame(rows).to_csv(FIXTURES / "dirty_data.csv", index=False)
    _write_gold(
        "dirty_data",
        {
            "source": "dirty_data",
            "row_node_label": "Cliente",
            "roles": {
                "Id Cliente": "node_key",
                "Nombre Completo": "attribute",
                "Categoría": "dimension",
                "Monto (USD)": "attribute",
                "Fecha Registro": "attribute",
                "país": "dimension",
            },
        },
    )


def gen_health_patients(rng: random.Random) -> None:
    """Dominio distinto (salud) para validar generalización."""
    genders = ["M", "F", "X"]
    depts = ["Cardiology", "Oncology", "Pediatrics", "Neurology", "ER"]
    blood = ["A+", "A-", "B+", "O+", "O-", "AB+"]
    diag = [f"ICD-{rng.randint(100,999)}" for _ in range(12)]
    rows = []
    for i in range(1, 71):
        rows.append(
            {
                "patient_id": i,
                "mrn": f"MRN{100000 + i}",
                "gender": rng.choice(genders),
                "age": rng.randint(0, 95),
                "admission_date": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
                "department": rng.choice(depts),
                "physician_id": rng.randint(1, 15),
                "diagnosis_code": rng.choice(diag),
                "blood_type": rng.choice(blood),
            }
        )
    pd.DataFrame(rows).to_csv(FIXTURES / "health_patients.csv", index=False)
    _write_gold(
        "health_patients",
        {
            "source": "health_patients",
            "row_node_label": "Patient",
            "roles": {
                "patient_id": "node_key",
                "mrn": "attribute",
                "gender": "dimension",
                "age": "attribute",
                "admission_date": "attribute",
                "department": "dimension",
                "physician_id": "relation_fk",
                "diagnosis_code": "dimension",
                "blood_type": "dimension",
            },
        },
    )


def gen_shop_relational(rng: random.Random) -> None:
    """XLSX multi-hoja relacional con join table (many-to-many)."""
    cities = ["Bogotá", "Medellín", "Cali"]
    segments = ["retail", "wholesale"]
    categories = ["Electronics", "Home", "Toys", "Books"]

    customers = [
        {
            "customer_id": c,
            "name": f"Customer {c:02d}",
            "city": rng.choice(cities),
            "segment": rng.choice(segments),
        }
        for c in range(1, 16)
    ]
    products = [
        {
            "product_id": p,
            "name": f"Product {p:02d}",
            "category": rng.choice(categories),
            "price": round(rng.uniform(5, 300), 2),
        }
        for p in range(1, 21)
    ]
    orders = [
        {
            "order_id": o,
            "customer_id": rng.randint(1, 15),
            "order_date": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "total": round(rng.uniform(20, 2000), 2),
        }
        for o in range(1, 41)
    ]
    order_items = []
    for o in range(1, 41):
        for _ in range(rng.randint(1, 4)):
            order_items.append(
                {
                    "order_id": o,
                    "product_id": rng.randint(1, 20),
                    "quantity": rng.randint(1, 5),
                }
            )

    path = FIXTURES / "shop_relational.xlsx"
    with pd.ExcelWriter(path) as w:
        pd.DataFrame(customers).to_excel(w, sheet_name="customers", index=False)
        pd.DataFrame(products).to_excel(w, sheet_name="products", index=False)
        pd.DataFrame(orders).to_excel(w, sheet_name="orders", index=False)
        pd.DataFrame(order_items).to_excel(w, sheet_name="order_items", index=False)

    _write_gold(
        "shop_relational",
        {
            "tables": [
                {
                    "source": "customers",
                    "row_node_label": "Customer",
                    "roles": {
                        "customer_id": "node_key",
                        "name": "attribute",
                        "city": "dimension",
                        "segment": "dimension",
                    },
                },
                {
                    "source": "products",
                    "row_node_label": "Product",
                    "roles": {
                        "product_id": "node_key",
                        "name": "attribute",
                        "category": "dimension",
                        "price": "attribute",
                    },
                },
                {
                    "source": "orders",
                    "row_node_label": "Order",
                    "roles": {
                        "order_id": "node_key",
                        "customer_id": "relation_fk",
                        "order_date": "attribute",
                        "total": "attribute",
                    },
                },
                {
                    "source": "order_items",
                    "row_node_label": "OrderItem",
                    "roles": {
                        "order_id": "relation_fk",
                        "product_id": "relation_fk",
                        "quantity": "attribute",
                    },
                },
            ]
        },
    )


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    gen_flat_employees(rng)
    gen_orders_fk(rng)
    gen_dirty_data(rng)
    gen_health_patients(rng)
    gen_shop_relational(rng)
    print(f"Fixtures generados en {FIXTURES}")


if __name__ == "__main__":
    main()
