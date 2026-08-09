"""
Caso de Uso: IngestTabularUseCase

Modo de ingesta *Schema-Guided Ingestion (SGI)* para datos tabulares/semi-estructurados
(CSV, XLSX). Corre en paralelo al ETI de texto, NO dentro de él: la estructura de una
tabla ya es explícita, así que no se chunkea ni se re-extrae con NLP.

Flujo:
1. Extract  — cargar la(s) tabla(s) vía TabularLoaderService.
2. Profile  — perfilar columnas (determinista).
3. Propose  — proponer mapeo columna→rol (heurística + LLM para lo dudoso).
4. Confirm  — si dry_run/no confirmado, retornar la propuesta SIN escribir.
5. Persist  — materializar filas como nodos/relaciones (idempotente).

Depende solo de interfaces del dominio (Clean Architecture).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ungraph.domain.repositories.tabular_repository import TabularRepository
from ungraph.domain.services.schema_inference_service import SchemaInferenceService
from ungraph.domain.services.tabular_loader_service import TabularLoaderService
from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import TabularSchemaProposal

logger = logging.getLogger(__name__)


@dataclass
class TabularIngestionResult:
    """Resultado de ``IngestTabularUseCase.execute``.

    Attributes:
        proposals: Propuesta de esquema por tabla (siempre presente).
        persisted: True si se escribió en el grafo (False en dry-run).
        stats: Estadísticas de persistencia por tabla (vacío en dry-run).
    """

    proposals: List[TabularSchemaProposal] = field(default_factory=list)
    persisted: bool = False
    stats: List[Dict[str, Any]] = field(default_factory=list)


class IngestTabularUseCase:
    """Ingesta de fuentes tabulares con inferencia de esquema y confirmación."""

    def __init__(
        self,
        tabular_loader_service: TabularLoaderService,
        schema_inference_service: SchemaInferenceService,
        tabular_repository: TabularRepository,
    ):
        self.tabular_loader_service = tabular_loader_service
        self.schema_inference_service = schema_inference_service
        self.tabular_repository = tabular_repository

    def execute(
        self,
        file_path: Path,
        *,
        dry_run: bool = True,
        mappings: Optional[List[TabularSchemaProposal]] = None,
        batch_size: int = 1000,
        **loader_kwargs: Any,
    ) -> TabularIngestionResult:
        """Ejecuta el pipeline SGI.

        Args:
            file_path: Archivo tabular (.csv/.xlsx).
            dry_run: Si True (default), solo propone el esquema y NO escribe en el grafo.
                El usuario revisa/edita la propuesta y vuelve a ejecutar con dry_run=False.
            mappings: Propuestas confirmadas/editadas a aplicar. Si se pasan, se usan en
                lugar de re-inferir (deben corresponder por ``source`` a las tablas).
            batch_size: Tamaño de lote para la persistencia UNWIND.

        Returns:
            ``TabularIngestionResult`` con las propuestas y, si no es dry-run, las stats.
        """
        file_path = Path(file_path)
        logger.info("SGI: cargando fuente tabular %s (dry_run=%s)", file_path, dry_run)

        # 1. Extract
        tables = self.tabular_loader_service.load(file_path, **loader_kwargs)
        if not tables:
            raise ValueError(f"No se cargó ninguna tabla desde {file_path}")

        # Índice de propuestas confirmadas por fuente (si se proporcionaron).
        confirmed = {p.source: p for p in (mappings or [])}

        result = TabularIngestionResult()
        sha = self._sha256(file_path)

        for table in tables:
            proposal = confirmed.get(table.name)
            if proposal is None:
                # 2. Profile + 3. Propose
                profiles = self.schema_inference_service.profile(table)
                proposal = self.schema_inference_service.propose_schema(table, profiles)
            result.proposals.append(proposal)

        # 4. Confirm gate
        if dry_run:
            logger.info("SGI dry-run: %s propuesta(s) generada(s), sin escritura.", len(result.proposals))
            return result

        # 5. Persist
        for table in tables:
            proposal = self._match_proposal(result.proposals, table)
            stats = self.tabular_repository.save_tabular(
                proposal, table, source_sha256=sha, batch_size=batch_size
            )
            result.stats.append(stats)
        result.persisted = True
        logger.info("SGI: persistidas %s tabla(s).", len(result.stats))
        return result

    @staticmethod
    def _match_proposal(
        proposals: List[TabularSchemaProposal], table: TabularData
    ) -> TabularSchemaProposal:
        for p in proposals:
            if p.source == table.name:
                return p
        # fallback: primera propuesta (caso mono-tabla)
        return proposals[0]

    @staticmethod
    def _sha256(file_path: Path) -> Optional[str]:
        try:
            return hashlib.sha256(file_path.read_bytes()).hexdigest()
        except OSError:
            return None
