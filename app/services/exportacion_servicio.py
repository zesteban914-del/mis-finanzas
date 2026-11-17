"""Exportar el reporte de un mes a CSV (todos los planes) o Excel (plan Pro)."""

import csv
import io
from datetime import date
from typing import Tuple

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy.orm import Session

from app.models import TipoMovimiento, Usuario
from app.repositories import RepositorioCajas, RepositorioCategorias, RepositorioMovimientos
from app.repositories.movimiento_repositorio import rango_del_mes
from app.services.autorizacion import exigir_caracteristica
from app.services.excepciones import ErrorDeValidacion
from app.services.reporte_servicio import ServicioReportes
from app.services.validaciones import validar_mes

COLUMNAS = ["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Caja", "Registrado por"]
TIPOS_CONTENIDO = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
FORMATO_PESOS = '"$"#,##0'


class ServicioExportacion:
    def __init__(self, db: Session, usuario: Usuario):
        self.usuario = usuario
        self.reportes = ServicioReportes(db, usuario)
        self.movimientos = RepositorioMovimientos(db, usuario.titular_id)
        self.categorias = RepositorioCategorias(db, usuario.titular_id)
        self.cajas = RepositorioCajas(db, usuario.titular_id)

    def exportar(self, mes: str, formato: str) -> Tuple[bytes, str, str]:
        """Devuelve (contenido, nombre del archivo, tipo de contenido)."""
        if formato not in TIPOS_CONTENIDO:
            raise ErrorDeValidacion("El formato debe ser csv o xlsx")
        if formato == "xlsx":
            exigir_caracteristica(self.usuario.plan_efectivo, "exportar_excel")
        anio, numero = validar_mes(mes)
        inicio, fin = rango_del_mes(anio, numero)
        filas = self._filas(inicio, fin)
        contenido = self._csv(filas) if formato == "csv" else self._excel(mes, filas)
        return contenido, f"reporte-{mes}.{formato}", TIPOS_CONTENIDO[formato]

    def _filas(self, inicio: date, fin: date) -> list:
        nombres_categoria = {c.id: c.nombre for c in self.categorias.listar()}
        nombres_caja = {c.id: c.nombre for c in self.cajas.listar()}
        movimientos = [
            m for m in self.movimientos.listar(fecha_inicio=inicio) if m.fecha < fin
        ]
        return [
            [
                m.fecha,
                "Ingreso" if m.tipo == TipoMovimiento.INGRESO else "Gasto",
                nombres_categoria.get(m.categoria_id, ""),
                m.descripcion,
                float(m.monto),
                nombres_caja.get(m.caja_id, ""),
                m.registrado_por_nombre or ("Automático" if m.recurrente_id else ""),
            ]
            for m in sorted(movimientos, key=lambda m: (m.fecha, m.id))
        ]

    @staticmethod
    def _csv(filas: list) -> bytes:
        # Punto y coma y coma decimal: así lo abre Excel en español sin pasos extra.
        salida = io.StringIO()
        escritor = csv.writer(salida, delimiter=";")
        escritor.writerow(COLUMNAS)
        for fila in filas:
            fila = list(fila)
            fila[0] = fila[0].isoformat()
            fila[4] = f"{fila[4]:.2f}".replace(".", ",")
            escritor.writerow(fila)
        return ("﻿" + salida.getvalue()).encode("utf-8")  # BOM: tildes correctas en Excel

    def _excel(self, mes: str, filas: list) -> bytes:
        libro = Workbook()
        negrita = Font(bold=True, color="FFFFFF")
        relleno = PatternFill("solid", fgColor="1C5CAB")

        resumen = libro.active
        resumen.title = "Resumen"
        datos = self.reportes.resumen_mensual(mes)
        resumen.append([f"Reporte de {mes}"])
        resumen["A1"].font = Font(bold=True, size=14)
        resumen.append([self.usuario.nombre_negocio or self.usuario.nombre])
        resumen.append([])
        for etiqueta, valor in (
            ("Ingresos", datos.total_ingresos),
            ("Gastos", datos.total_gastos),
            ("Balance", datos.balance),
        ):
            resumen.append([etiqueta, float(valor)])
            resumen.cell(resumen.max_row, 2).number_format = FORMATO_PESOS
        resumen.append([])
        resumen.append(["Categoría", "Ingresos", "Gastos"])
        for celda in resumen[resumen.max_row]:
            celda.font, celda.fill = negrita, relleno
        for c in datos.categorias:
            resumen.append([c.categoria, float(c.total_ingresos), float(c.total_gastos)])
            for columna in (2, 3):
                resumen.cell(resumen.max_row, columna).number_format = FORMATO_PESOS
        resumen.column_dimensions["A"].width = 28
        resumen.column_dimensions["B"].width = 18
        resumen.column_dimensions["C"].width = 18

        hoja = libro.create_sheet("Movimientos")
        hoja.append(COLUMNAS)
        for celda in hoja[1]:
            celda.font, celda.fill = negrita, relleno
            celda.alignment = Alignment(horizontal="center")
        for fila in filas:
            hoja.append(fila)
            hoja.cell(hoja.max_row, 1).number_format = "DD/MM/YYYY"
            hoja.cell(hoja.max_row, 5).number_format = FORMATO_PESOS
        for columna, ancho in zip("ABCDEFG", (12, 10, 22, 36, 16, 18, 20)):
            hoja.column_dimensions[columna].width = ancho
        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions

        salida = io.BytesIO()
        libro.save(salida)
        return salida.getvalue()
