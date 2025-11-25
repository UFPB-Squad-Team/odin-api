from motor.motor_asyncio import AsyncIOMotorClient
from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from ..mapper.school_mapper import MongoSchoolMapper
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
import re
from pymongo.collation import Collation


class MongoSchoolRepository(ISchoolRepository):
    """
    MongoDB implementation of the School repository using Motor.
    """

    def __init__(self, collection: AsyncIOMotorClient):
        self.collection = collection

    async def list_all(
        self,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[School]:
        cursor = (
            self.collection.find()
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        schools_docs = await cursor.to_list(length=page_size)
        schools = MongoSchoolMapper.to_domain_many(schools_docs)
        total = await self.collection.count_documents({})

        return PaginatedResponse[School](
            items=schools,
            total_items=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(self, school_id: str) -> Optional[School]:
        query = {"_id": school_id}
        if ObjectId.is_valid(school_id):
            query = {"_id": ObjectId(school_id)}

        document = await self.collection.find_one(query)

        if not document and ObjectId.is_valid(school_id):
             document = await self.collection.find_one({"_id": school_id})

        if not document:
            return None
        return MongoSchoolMapper.to_domain(document)

    async def fuzzy_search(
        self,
        query: str,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[School]:
        """
        Orchestrates the fuzzy search logic by delegating complex tasks 
        to private helper methods.
        """
        query = query.strip()
        search_collation = Collation(locale='pt', strength=1)

        if query.isdigit():
            mongo_filter = self._build_numeric_filter(query)
            state_score_conditions = []
            city_score_conditions = []
        else:
            mongo_filter, state_score_conditions, city_score_conditions = \
                self._build_text_search_conditions(query)

        total = await self.collection.count_documents(
            mongo_filter, 
            collation=search_collation
        )

        pipeline = self._build_aggregation_pipeline(
            mongo_filter=mongo_filter,
            state_scores=state_score_conditions,
            city_scores=city_score_conditions,
            page=page,
            page_size=page_size
        )

        cursor = self.collection.aggregate(pipeline, collation=search_collation)
        schools_docs = await cursor.to_list(length=page_size)
        schools = MongoSchoolMapper.to_domain_many(schools_docs)

        return PaginatedResponse[School](
            items=schools,
            total_items=total,
            page=page,
            page_size=page_size,
        )
    
    def _build_numeric_filter(self, query: str) -> Dict[str, Any]:
        """Builds a simple exact match filter for numeric IDs."""
        return {
            "$or": [
                {"escolaIdInep": int(query)},
                {"municipioIdIbge": int(query)}
            ]
        }

    def _build_text_search_conditions(
        self, 
        query: str
    ) -> Tuple[Dict[str, Any], List[Dict], List[Dict]]:
        """
        Processes the text query to generate:
        1. The MongoDB filter ($match)
        2. The scoring conditions for State
        3. The scoring conditions for City
        """
        terms = query.split()
        and_conditions = []
        state_score_conditions = []
        city_score_conditions = []

        for term in terms:
            regex = re.compile(re.escape(term), re.IGNORECASE)
            
            or_conditions = [
                {"escolaNome": regex},
                {"municipioNome": regex},
                {"estadoSigla": regex},
                {"estadoNome": regex},
                {"dependenciaAdm": regex},
                {"tipoLocalizacao": regex}
            ]
            and_conditions.append({"$or": or_conditions})

            state_score_conditions.append({
                "$cond": {
                    "if": { 
                        "$regexMatch": { 
                            "input": "$estadoNome",
                            "regex": regex.pattern, 
                            "options": "i"
                        } 
                    },
                    "then": 1, "else": 0
                }
            })

            city_score_conditions.append({
                "$cond": {
                    "if": { 
                        "$regexMatch": { 
                            "input": "$municipioNome", 
                            "regex": regex.pattern, 
                            "options": "i"
                        } 
                    },
                    "then": 1, "else": 0
                }
            })
        
        mongo_filter = {"$and": and_conditions} if and_conditions else {}
        
        return mongo_filter, state_score_conditions, city_score_conditions

    def _build_aggregation_pipeline(
        self,
        mongo_filter: Dict[str, Any],
        state_scores: List[Dict],
        city_scores: List[Dict],
        page: int,
        page_size: int
    ) -> List[Dict[str, Any]]:
        """Constructs the aggregation pipeline stages."""
        
        return [
            {"$match": mongo_filter},

            {"$addFields": {
                "rawStateScore": { "$sum": state_scores if state_scores else [0] },
                "rawCityScore":  { "$sum": city_scores  if city_scores  else [0] }
            }},

            {"$addFields": {
                "finalScore": {
                    "$add": [
                        { "$multiply": ["$rawStateScore", 1000] },
                        "$rawCityScore"
                    ]
                }
            }},

            {"$sort": {
                "finalScore": -1,
                "estadoSigla": 1,
                "municipioNome": 1,
                "escolaNome": 1
            }},

            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
            {"$project": {"rawStateScore": 0, "rawCityScore": 0, "finalScore": 0}}
        ]