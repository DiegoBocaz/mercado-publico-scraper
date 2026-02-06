#!/usr/bin/env python3
"""
Tender Explorer - Motor de Exploración Detallada de Licitaciones
Permite explorar y analizar licitaciones específicas en profundidad
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from loguru import logger
import json


@dataclass
class TenderDetails:
    """Detalles completos de una licitación"""
    codigo: str
    nombre: str
    descripcion: str
    organismo: str
    fecha_publicacion: str
    fecha_cierre: str
    monto_estimado: float
    estado: str
    region: str
    items: List[Dict] = None
    ofertas: List[Dict] = None
    documentos: List[Dict] = None
    contacto: Dict = None
    bases_administrativas: Optional[str] = None
    bases_tecnicas: Optional[str] = None


class TenderExplorer:
    """Explorador detallado de licitaciones"""
    
    API_BASE = "https://api.mercadopublico.cl/servicios/v1/publico"
    WEB_BASE = "https://www.mercadopublico.cl"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0'
        })
        self.driver = None
    
    def explore_tender(self, codigo_licitacion: str) -> TenderDetails:
        """
        Explora una licitación en detalle
        
        Args:
            codigo_licitacion: Código de la licitación
        
        Returns:
            TenderDetails con toda la información
        """
        logger.info(f"Explorando licitación: {codigo_licitacion}")
        
        try:
            # 1. Obtener datos básicos de la API
            basic_info = self._get_basic_info(codigo_licitacion)
            if not basic_info:
                logger.error(f"No se encontró licitación: {codigo_licitacion}")
                return None
            
            tender = TenderDetails(
                codigo=codigo_licitacion,
                nombre=basic_info.get('Nombre', ''),
                descripcion=basic_info.get('Descripcion', ''),
                organismo=basic_info.get('Organismo', {}).get('Nombre', ''),
                fecha_publicacion=basic_info.get('FechaPublicacion', ''),
                fecha_cierre=basic_info.get('FechaCierre', ''),
                monto_estimado=float(basic_info.get('MontoEstimado', 0)),
                estado=basic_info.get('Estado', ''),
                region=basic_info.get('Region', '')
            )
            
            # 2. Obtener items/productos
            logger.debug("Obteniendo items...")
            tender.items = self._get_items(codigo_licitacion)
            
            # 3. Obtener ofertas si está cerrada
            if 'cerrada' in tender.estado.lower():
                logger.debug("Obteniendo ofertas...")
                tender.ofertas = self._get_offers(codigo_licitacion)
            
            # 4. Obtener información de contacto
            logger.debug("Obteniendo contacto...")
            tender.contacto = self._get_contact_info(codigo_licitacion)
            
            logger.success(f"Licitación explorada exitosamente: {codigo_licitacion}")
            return tender
            
        except Exception as e:
            logger.error(f"Error explorando licitación: {e}")
            return None
    
    def _get_basic_info(self, codigo: str) -> Dict:
        """Obtiene información básica de la API"""
        try:
            endpoint = f"{self.API_BASE}/licitaciones.json"
            params = {"codigo": codigo}
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            listado = data.get('Listado', [])
            
            return listado[0] if listado else None
            
        except Exception as e:
            logger.warning(f"Error obteniendo info básica: {e}")
            return None
    
    def _get_items(self, codigo: str) -> List[Dict]:
        """Obtiene los items/productos de la licitación"""
        try:
            endpoint = f"{self.API_BASE}/licitaciones/items.json"
            params = {"codigo": codigo}
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('Listado', [])
            
        except Exception as e:
            logger.warning(f"Error obteniendo items: {e}")
            return []
    
    def _get_offers(self, codigo: str) -> List[Dict]:
        """Obtiene las ofertas presentadas"""
        try:
            endpoint = f"{self.API_BASE}/licitaciones/ofertas.json"
            params = {"codigo": codigo}
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('Listado', [])
            
        except Exception as e:
            logger.warning(f"Error obteniendo ofertas: {e}")
            return []
    
    def _get_contact_info(self, codigo: str) -> Dict:
        """Obtiene información de contacto de la licitación"""
        try:
            endpoint = f"{self.API_BASE}/licitaciones/contacto.json"
            params = {"codigo": codigo}
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('Contacto', {})
            
        except Exception as e:
            logger.warning(f"Error obteniendo contacto: {e}")
            return {}
    
    def compare_tenders(self, codigos: List[str]) -> Dict:
        """
        Compara múltiples licitaciones lado a lado
        
        Args:
            codigos: Lista de códigos de licitaciones
        
        Returns:
            Dict con comparación de licitaciones
        """
        logger.info(f"Comparando {len(codigos)} licitaciones")
        
        tenders = []
        for codigo in codigos:
            tender = self.explore_tender(codigo)
            if tender:
                tenders.append(tender)
        
        if not tenders:
            logger.warning("No se encontraron licitaciones para comparar")
            return {}
        
        comparison = {
            'total': len(tenders),
            'montos': {
                'minimo': min(t.monto_estimado for t in tenders),
                'maximo': max(t.monto_estimado for t in tenders),
                'promedio': sum(t.monto_estimado for t in tenders) / len(tenders),
            },
            'por_estado': self._group_by_state(tenders),
            'por_region': self._group_by_region(tenders),
            'por_organismo': self._group_by_organism(tenders),
        }
        
        logger.success(f"Comparación completada: {len(tenders)} licitaciones")
        return comparison
    
    def _group_by_state(self, tenders: List[TenderDetails]) -> Dict:
        """Agrupa licitaciones por estado"""
        by_state = {}
        for tender in tenders:
            state = tender.estado
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(tender.codigo)
        return by_state
    
    def _group_by_region(self, tenders: List[TenderDetails]) -> Dict:
        """Agrupa licitaciones por región"""
        by_region = {}
        for tender in tenders:
            region = tender.region
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(tender.codigo)
        return by_region
    
    def _group_by_organism(self, tenders: List[TenderDetails]) -> Dict:
        """Agrupa licitaciones por organismo"""
        by_org = {}
        for tender in tenders:
            org = tender.organismo
            if org not in by_org:
                by_org[org] = []
            by_org[org].append(tender.codigo)
        return by_org
    
    def export_to_json(self, tender: TenderDetails, filepath: str):
        """
        Exporta detalles de licitación a JSON
        
        Args:
            tender: Objeto TenderDetails
            filepath: Ruta del archivo
        """
        data = {
            'codigo': tender.codigo,
            'nombre': tender.nombre,
            'descripcion': tender.descripcion,
            'organismo': tender.organismo,
            'fecha_publicacion': tender.fecha_publicacion,
            'fecha_cierre': tender.fecha_cierre,
            'monto_estimado': tender.monto_estimado,
            'estado': tender.estado,
            'region': tender.region,
            'items': tender.items or [],
            'ofertas': tender.ofertas or [],
            'contacto': tender.contacto or {},
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.success(f"Licitación exportada a: {filepath}")
    
    def generate_report(self, tender: TenderDetails) -> str:
        """
        Genera reporte detallado de una licitación
        
        Returns:
            String con reporte formateado
        """
        report = f"""
        ═══════════════════════════════════════════════════════════
        REPORTE DE LICITACIÓN: {tender.codigo}
        ═══════════════════════════════════════════════════════════
        
        INFORMACIÓN GENERAL:
        ───────────────────────────────────────────────────────────
        Nombre: {tender.nombre}
        Estado: {tender.estado}
        Región: {tender.region}
        Monto Estimado: ${tender.monto_estimado:,.0f}
        
        ORGANISMOS Y CONTACTO:
        ───────────────────────────────────────────────────────────
        Organismo: {tender.organismo}
        Contacto: {tender.contacto.get('Nombre', 'N/A')} 
                  {tender.contacto.get('Email', 'N/A')}
                  {tender.contacto.get('Telefono', 'N/A')}
        
        FECHAS IMPORTANTES:
        ───────────────────────────────────────────────────────────
        Publicación: {tender.fecha_publicacion}
        Cierre de Ofertas: {tender.fecha_cierre}
        
        DESCRIPCIÓN:
        ───────────────────────────────────────────────────────────
        {tender.descripcion[:500]}...
        
        ITEMS/PRODUCTOS ({len(tender.items or [])}):
        ───────────────────────────────────────────────────────────
        """
        
        if tender.items:
            for item in tender.items[:5]:
                report += f"\n  • {item.get('Descripcion', 'N/A')} (Qty: {item.get('Cantidad', 'N/A')})"
        
        if tender.ofertas:
            report += f"\n\n        OFERTAS RECIBIDAS ({len(tender.ofertas)}):\n"
            for oferta in tender.ofertas[:5]:
                report += f"\n  • {oferta.get('Proveedor', 'N/A')}: ${oferta.get('Monto', 'N/A'):,.0f}"
        
        report += "\n\n        ═══════════════════════════════════════════════════════════\n"
        
        return report
    
    def close(self):
        """Cierra conexiones"""
        if self.driver:
            self.driver.quit()
        self.session.close()
        logger.info("Conexiones cerradas")
