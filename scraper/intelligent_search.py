#!/usr/bin/env python3
"""
Motor de Búsqueda Inteligente de Licitaciones
Busca y clasifica licitaciones basándose en criterios de experiencia profesional
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import requests
from loguru import logger
import re
from collections import defaultdict


@dataclass
class ExperienceProfile:
    """Perfil de experiencia profesional para matching"""
    
    # Habilidades técnicas
    technical_skills: List[str] = field(default_factory=list)
    
    # Tecnologías específicas
    technologies: List[str] = field(default_factory=list)
    
    # Sectores de experiencia
    sectors: List[str] = field(default_factory=list)
    
    # Palabras clave principales
    primary_keywords: List[str] = field(default_factory=list)
    
    # Palabras clave secundarias
    secondary_keywords: List[str] = field(default_factory=list)
    
    # Años de experiencia
    years_experience: int = 0
    
    # Rangos de monto preferidos (en CLP)
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    
    # Regiones de interés
    regions: List[str] = field(default_factory=list)


class IntelligentTenderSearch:
    """Motor de búsqueda inteligente de licitaciones"""
    
    API_BASE = "https://api.mercadopublico.cl/servicios/v1/publico"
    WEB_BASE = "https://www.mercadopublico.cl"
    
    def __init__(self, experience_profile: ExperienceProfile):
        self.profile = experience_profile
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
    
    def search_by_experience(
        self,
        days_back: int = 30,
        max_results: int = 100,
        min_relevance_score: int = 60
    ) -> List[Dict]:
        """
        Busca licitaciones basándose en perfil de experiencia
        
        Args:
            days_back: Días hacia atrás para buscar
            max_results: Número máximo de resultados
            min_relevance_score: Score mínimo de relevancia (0-100)
        
        Returns:
            Lista de licitaciones ordenadas por relevancia
        """
        logger.info("Iniciando búsqueda inteligente de licitaciones")
        
        # 1. Generar búsquedas múltiples basadas en perfil
        search_queries = self._generate_search_queries()
        
        all_tenders = []
        seen_codes = set()
        
        # 2. Ejecutar búsquedas
        for query in search_queries:
            try:
                tenders = self._search_api(
                    keywords=query,
                    days_back=days_back
                )
                
                for tender in tenders:
                    code = tender.get('Codigo', '')
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        all_tenders.append(tender)
                        
            except Exception as e:
                logger.error(f"Error en búsqueda '{query}': {e}")
                continue
        
        logger.info(f"Encontradas {len(all_tenders)} licitaciones únicas")
        
        # 3. Calcular relevancia y filtrar
        scored_tenders = []
        for tender in all_tenders:
            score = self._calculate_relevance_score(tender)
            
            if score >= min_relevance_score:
                tender['relevance_score'] = score
                tender['match_reasons'] = self._get_match_reasons(tender)
                scored_tenders.append(tender)
        
        # 4. Ordenar por relevancia
        scored_tenders.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.success(
            f"Filtradas {len(scored_tenders)} licitaciones relevantes "
            f"(score >= {min_relevance_score})"
        )
        
        return scored_tenders[:max_results]
    
    def _generate_search_queries(self) -> List[str]:
        """Genera consultas de búsqueda basadas en el perfil"""
        queries = []
        
        # Agregar keywords primarias
        queries.extend(self.profile.primary_keywords)
        
        # Agregar tecnologías específicas
        queries.extend(self.profile.technologies)
        
        # Agregar habilidades técnicas (primeras 5)
        queries.extend(self.profile.technical_skills[:5])
        
        # Remover duplicados y convertir a minúsculas
        queries = list(set([q.lower().strip() for q in queries if q]))
        
        logger.debug(f"Generadas {len(queries)} consultas de búsqueda")
        return queries
    
    def _search_api(
        self,
        keywords: str,
        days_back: int = 30
    ) -> List[Dict]:
        """Busca en la API oficial de Mercado Público"""
        
        fecha_desde = (datetime.now() - timedelta(days=days_back)).strftime("%d%m%Y")
        fecha_hasta = datetime.now().strftime("%d%m%Y")
        
        endpoint = f"{self.API_BASE}/licitaciones.json"
        
        params = {
            "codigo": keywords,
            "fecha": fecha_desde,
            "fecha_final": fecha_hasta,
            "estado": "5",  # Publicada
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get("Listado", [])
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error en API para '{keywords}': {e}")
            return []
    
    def _calculate_relevance_score(self, tender: Dict) -> int:
        """Calcula score de relevancia (0-100) basado en el perfil"""
        score = 0
        
        # Obtener textos para análisis
        nombre = tender.get('Nombre', '').lower()
        descripcion = tender.get('Descripcion', '').lower()
        full_text = f"{nombre} {descripcion}"
        
        # 1. Keywords primarias (máx 30 puntos)
        primary_matches = sum(
            1 for kw in self.profile.primary_keywords 
            if kw.lower() in full_text
        )
        score += min(primary_matches * 10, 30)
        
        # 2. Keywords secundarias (máx 15 puntos)
        secondary_matches = sum(
            1 for kw in self.profile.secondary_keywords 
            if kw.lower() in full_text
        )
        score += min(secondary_matches * 5, 15)
        
        # 3. Tecnologías específicas (máx 20 puntos)
        tech_matches = sum(
            1 for tech in self.profile.technologies 
            if tech.lower() in full_text
        )
        score += min(tech_matches * 7, 20)
        
        # 4. Habilidades técnicas (máx 15 puntos)
        skill_matches = sum(
            1 for skill in self.profile.technical_skills 
            if skill.lower() in full_text
        )
        score += min(skill_matches * 5, 15)
        
        # 5. Sector de experiencia (máx 10 puntos)
        organismo = tender.get('Organismo', {}).get('Nombre', '').lower()
        sector_matches = sum(
            1 for sector in self.profile.sectors 
            if sector.lower() in organismo or sector.lower() in full_text
        )
        score += min(sector_matches * 5, 10)
        
        # 6. Región de interés (5 puntos)
        region = tender.get('Region', '')
        if region in self.profile.regions or 'todas' in [r.lower() for r in self.profile.regions]:
            score += 5
        
        # 7. Monto en rango (5 puntos)
        try:
            monto = int(tender.get('MontoEstimado', 0))
            if self.profile.min_amount and self.profile.max_amount:
                if self.profile.min_amount <= monto <= self.profile.max_amount:
                    score += 5
        except (ValueError, TypeError):
            pass
        
        return min(score, 100)
    
    def _get_match_reasons(self, tender: Dict) -> List[str]:
        """Obtiene las razones por las que una licitación es relevante"""
        reasons = []
        
        nombre = tender.get('Nombre', '').lower()
        descripcion = tender.get('Descripcion', '').lower()
        full_text = f"{nombre} {descripcion}"
        
        # Keywords primarias encontradas
        primary_found = [
            kw for kw in self.profile.primary_keywords 
            if kw.lower() in full_text
        ]
        if primary_found:
            reasons.append(f"Keywords principales: {', '.join(primary_found[:3])}")
        
        # Tecnologías encontradas
        tech_found = [
            tech for tech in self.profile.technologies 
            if tech.lower() in full_text
        ]
        if tech_found:
            reasons.append(f"Tecnologías: {', '.join(tech_found[:3])}")
        
        # Habilidades encontradas
        skills_found = [
            skill for skill in self.profile.technical_skills 
            if skill.lower() in full_text
        ]
        if skills_found:
            reasons.append(f"Habilidades: {', '.join(skills_found[:3])}")
        
        return reasons
    
    def get_statistics(self, tenders: List[Dict]) -> Dict:
        """Genera estadísticas sobre las licitaciones encontradas"""
        if not tenders:
            return {}
        
        stats = {
            'total': len(tenders),
            'avg_relevance': sum(t.get('relevance_score', 0) for t in tenders) / len(tenders),
            'by_region': defaultdict(int),
            'by_organismo_type': defaultdict(int),
            'avg_amount': 0,
            'total_amount': 0,
        }
        
        montos = []
        for tender in tenders:
            # Por región
            region = tender.get('Region', 'Sin especificar')
            stats['by_region'][region] += 1
            
            # Por tipo de organismo
            org_nombre = tender.get('Organismo', {}).get('Nombre', '')
            if 'municipalid' in org_nombre.lower():
                stats['by_organismo_type']['Municipalidades'] += 1
            elif 'servicio' in org_nombre.lower():
                stats['by_organismo_type']['Servicios Públicos'] += 1
            else:
                stats['by_organismo_type']['Otros'] += 1
            
            # Montos
            try:
                monto = int(tender.get('MontoEstimado', 0))
                if monto > 0:
                    montos.append(monto)
            except (ValueError, TypeError):
                pass
        
        if montos:
            stats['avg_amount'] = sum(montos) / len(montos)
            stats['total_amount'] = sum(montos)
        
        return dict(stats)
