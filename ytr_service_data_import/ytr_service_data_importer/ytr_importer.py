# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 09:40:06 2021

@author: joonas.itkonen
"""
import os
from pymongo import MongoClient, DESCENDING
import requests
import json
import time
import urllib
import math
import pickle
from datetime import datetime
from typing import Optional
import logging
API = "http://{}:{}/palvelutieto/api/v1".format(
                os.environ.get("KOMPASSIYTR_HOST"),
                os.environ.get("KOMPASSIYTR_PORT"))
TG_MAP = {"KR-1": "KR1.1", "KR-2": "KR1.2", "KR-3": "KR1.3", "KR-4": "KR1"}
PROVINCE_CODES = ["02"]
suitable_target_groups = ['KR1', 'KR1.2']
nonsuitable_target_groups = ['KR1.1', 'KR1.3']

class YTRImporter():
    """
    A class to fetch data from Kompassi YTR

    Args
    ----------
    mongo_client : MongoClient ( default None )
        MongoDB client where service data is stored

    api_session : requests.Session ( default None )
        A requests session to send requests to PTV API

    Methods
    -------      
    import_services()
        Does nothing yet

    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None, api_session: Optional[requests.Session] = None) -> None:
        if mongo_client is None:        
            self.mongo_client = MongoClient("mongodb://{}:{}@{}:{}/{}".format(
                os.environ.get("MONGO_USERNAME"),
                os.environ.get("MONGO_PASSWORD"),
                os.environ.get("MONGO_HOST"),
                os.environ.get("MONGO_PORT"),
                os.environ.get("MONGO_DB")),
                ssl=True,
                tlsInsecure=True,
                replicaSet="globaldb",
                retrywrites=False,
                maxIdleTimeMS=120000,
                appName="@{}@".format(os.environ.get("MONGO_USERNAME"))
                )
        else:
            self.mongo_client = mongo_client
        
        # Init DB api session
        if api_session is None:
            self.api_session = requests.Session()
        else:
            self.api_session = api_session
        self.ptv_municipalities = list(self.mongo_client.service_db.municipalities.find({}))
            

    def _parse_service_info(self, service: dict) -> dict:
        service_final = {}
        service_id = service.get('id')
        if service_id is not None:
            service_id = str(service_id)
        service_final['id'] = str(service_id)
        
        service_final['ptvId'] = self._get_ptv_service_id(service)
        
        service_type = "Service"
        service_final['type'] = service_type
        service_subtype = None
        service_final['subtype'] = service_subtype
        
        channel_ids = [str(s_cha_id) for s_cha_id in service.get('palvelukanavat', [])]
        service_final['channelIds'] = channel_ids
        
        organization_id = service.get('toimija_id')
        if organization_id is not None:
            organization_id = str(organization_id)
        organization_elements = [{'name': None, 'id': organization_id}]        
        service_final['organizations'] = organization_elements
            
        languages = ['en', 'fi', 'sv']
        language_division = {'en': None, 'fi': None, 'sv': None}
        service_final['name'] = language_division.copy()
        service_final['descriptions'] = language_division.copy()
        service_final['requirement'] = language_division.copy()
        service_final['targetGroups'] = language_division.copy()
        service_final['serviceClasses'] = language_division.copy()
        service_final['areas'] = language_division.copy()
        service_final['lifeEvents'] = language_division.copy()
        # Divided by language    
        for language in languages:
            names = [service.get('nimi', {}).get(language)]
            names = [l_name for l_name in names if l_name is not None]
            if len(names) > 0:
                name = ' - '.join(names)
            else:
                name = None
            service_final['name'][language] = name
            descriptions = [{'value': service.get('kuvaus', {}).get(language), 'type': 'Description'}]
            descriptions = [d for d in descriptions if d['value'] is not None]
            service_final['descriptions'][language] = descriptions
            
            service_final['requirement'][language] = ''
            
            # Target groups
            target_groups = service.get('kohderyhmat', [])
            target_group_elements = []
            for target_group in target_groups:
                target_group_name = target_group.get('nimi').get(language)
                target_group_code = TG_MAP.get(target_group.get('koodi'))
                if target_group_code is None:
                    raise Exception("Unrecognized target group {}".format(target_group.get('koodi')))
                
                target_group_el = {"name": target_group_name,
                                   "code": target_group_code}
                target_group_elements.append(target_group_el) 
            service_final['targetGroups'][language] = target_group_elements
    
            # Service classes
            service_final['serviceClasses'][language] = []
                
            # Areas
            areas = service.get('kuntasaatavuudet', [])
            area_elements = []
            for area in areas:
                area_type = 'Municipality'
                area_id = area.get('kunta')
                area_code = self.municipality_map.get(area_id)
                municipality_element = [mun for mun in self.ptv_municipalities if mun.get('id') == area_code]
                if len(municipality_element) > 0:
                    area_name = municipality_element[0].get('name').get(language)
                else:
                    area_name = None

                area_el = {"name": area_name,
                           "type": area_type,
                           "code": area_code}
                area_elements.append(area_el)
            service_final['areas'][language] = area_elements
            
            # Life events
            service_final['lifeEvents'][language] = []
            
        if 'muutettu' in service.keys() and service.get('muutettu') is not None:
            service_final['lastUpdated'] = datetime.strptime(service.get('muutettu'), "%Y-%m-%dT%H:%M.%S.%fZ")
        else:
            service_final['lastUpdated'] = None
            
        return(service_final)      
    
    
    def _parse_channel_info(self, channel: dict) -> dict:
                        
        channel_final = {}
        
        channel_id = channel.get('id')
        if channel_id is not None:
            channel_id = str(channel_id)
        channel_final['id'] = channel_id
        
        channel_final['ptvId'] = self._get_ptv_channel_id(channel)

        area_type = 'Municipality'
        channel_final['areaType'] = area_type
        
        channel_final['type'] = None
        
        channel_final['serviceIds'] = []
        
        organization_id = channel.get('toimija')
        if organization_id is not None:
            organization_id = str(organization_id)
        channel_final['organizationId'] = organization_id

        languages = ['en', 'fi', 'sv']
        language_division = {'en': None, 'fi': None, 'sv': None}
        channel_final['name'] = language_division.copy()
        channel_final['descriptions'] = language_division.copy()
        channel_final['webPages'] = language_division.copy()
        channel_final['emails'] = language_division.copy()
        channel_final['phoneNumbers'] = language_division.copy()
        channel_final['addresses'] = language_division.copy()
        channel_final['areas'] = language_division.copy()
        channel_final['channelUrls'] = language_division.copy()
        channel_final['organizations'] = language_division.copy()
        
        # Divided by language    
        for language in languages:
            
            if 'nimi' in channel.keys():
                names = [channel.get('nimi').get(language)]
                names = [l_name for l_name in names if l_name is not None]
                if len(names) > 0:
                    name = ' - '.join(names)
                else:
                    name = None
            else:
                name = None
            channel_final['name'][language] = name
            
            if 'kuvaus' in channel.keys():
                descriptions = [{'value': channel.get('kuvaus').get(language), 'type': 'Description'}]
                descriptions = [d for d in descriptions if d['value'] is not None]
            else:
                descriptions = []
            channel_final['descriptions'][language] = descriptions
        
            channel_types = channel.get('yhteystiedot')
            channel_final['phoneNumbers'][language] = []
            channel_final['webPages'][language] = []
            channel_final['emails'][language] = []
            if channel_types is not None:
                for channel_type in channel_types:
                    if 'yhteystietotyyppi' in channel_type.keys():
                        if channel_type.get('yhteystietotyyppi').get('id') == 1:
                            if channel_type.get('arvo') is not None:
                                phone_numbers = [{'number': channel_type.get('arvo'),
                                                  'prefixNumber': None,
                                                  'chargeDescription': None,
                                                  'serviceChargeType': None}]
                            else:
                                phone_numbers = []
                            channel_final['phoneNumbers'][language] = phone_numbers
                        elif channel_type.get('yhteystietotyyppi').get('id') == 2:
                            if channel_type.get('arvo') is not None:
                                web_pages = [channel_type.get('arvo')]
                            else:
                                web_pages = []
                            channel_final['webPages'][language] = web_pages        
                
            # Addresses
            if channel.get('osoite') is not None:
                addresses = [channel.get('osoite')]
            else:
                addresses = []
            address_elements = []
            for address in addresses:
                if address.get('katuosoite') is not None:
                    street_address = address.get('katuosoite').get(language)
                else:
                    street_address = None                
                if address.get('postinumero') is not None:    
                    postal_code = address.get('postinumero')
                else:
                    postal_code = None
                    
                mun_id = address.get('kunta')
                municipality_code = self.municipality_map.get(mun_id)
                municipality_element = [mun for mun in self.ptv_municipalities if mun.get('id') == municipality_code]
                if len(municipality_element) > 0: 
                    municipality_name = municipality_element[0].get('name').get(language)
                else:
                    municipality_name = None

                address_el = {"streetName": street_address,
                                   "postalCode": postal_code,
                                   "municipalityCode": municipality_code,
                                   "municipalityName": municipality_name,
                                   "type": None,
                                   "subtype": None,
                                   "streetNumber": None,
                                   "latitude": None,
                                   "longitude": None,
                                   "postOffice": None}
                address_elements.append(address_el)
            channel_final['addresses'][language] = address_elements
                
            channel_final['areas'][language] = []
        if 'muutettu' in channel.keys() and channel.get('muutettu') is not None:
            channel_final['lastUpdated'] = datetime.strptime(channel.get('muutettu'), "%Y-%m-%dT%H:%M.%S.%fZ")
        else:
            channel_final['lastUpdated'] = None
        return(channel_final)
    
    def _parse_municipality_map(self, municipalities: list) -> dict:
        mun_map = {}
        for municipality in municipalities:
            municipality_id = municipality.get("id")
            municipality_code = municipality.get("kuntakoodi")
            if municipality_id is not None and municipality_code is not None:
                mun_map[municipality_id] = municipality_code
        return(mun_map)
    
    def _is_suitable_service(self, service: dict) -> bool:

        service_areas = service.get('areas')['fi']
        province_match = True
        municipality_match = True
        if len(service_areas) > 0:
            municipality_codes = [mun.get('id') for mun in self.ptv_municipalities]
            province_codes = PROVINCE_CODES
            address_municipality_codes = [area.get('code') for area in service_areas if area.get('type') == 'Municipality']
            address_province_codes = [area.get('code') for area in service_areas if area.get('type') == 'Province' or area.get('type') == 'Region']
            province_match = any([True for pro_code in address_province_codes if pro_code in province_codes])
            municipality_match = any([True for mun_code in address_municipality_codes if mun_code in municipality_codes])
        region_OK = province_match or municipality_match           
        service_tg_codes = [t_group.get('code') for t_group in service.get('targetGroups')['fi']]
        contains_suitable = True
        if len(service_tg_codes) > 0:
            contains_suitable = any([True for tg_code in service_tg_codes if tg_code in suitable_target_groups])
            tg_OK = contains_suitable
        return(tg_OK and region_OK)
    
    def _filter_and_split_services(self, services: list, ptv_services) -> tuple:

        ptv_ids = [ptv_service.get('id') for ptv_service in ptv_services]
        ytr_originals = [service for service in services if service.get('ptvId') is None]
        ptv_fetched = [service for service in services if service.get('ptvId') is not None]
        ptv_services_filtered = []
        for service in ptv_fetched:
            ptv_id = service.get('ptvId')
            if ptv_id in ptv_ids:
                ptv_service = [ptv_ser for ptv_ser in ptv_services if ptv_id == ptv_ser.get('id')][0].copy()
                ptv_service['ptvId'] = ptv_service.get('id')
                ptv_service['id'] = service.get('id')
                ptv_service['organizations'] = service.get('organizations')
                ptv_service['channelIds'] = service.get('channelIds')
                ptv_services_filtered.append(ptv_service)
            else:
                ytr_service = service.copy()
                ytr_service['ptvId'] = None
                ytr_originals.append(ytr_service)
        return ytr_originals, ptv_services_filtered
    
    
    def _split_channels(self, channels: list, old_channels: list, ptv_channels) -> tuple:
        
        ptv_ids = [ptv_channel.get('id') for ptv_channel in ptv_channels]
        matched_ptv_ids = [old_cha.get('ptvId') for old_cha in old_channels if old_cha.get('ptvId') is not None]
        matched_ytr_ids = [old_cha.get('id') for old_cha in old_channels if old_cha.get('id') is not None]
        new_channels = []
        known_channels = []
        for channel in channels:
            ytr_id = channel.get('id') 
            ptv_id = channel.get('ptvId')
            if ptv_id in matched_ptv_ids or ytr_id in matched_ytr_ids:
                # A channel that has been found earlier
                known_channels.append(channel)
            else:
                # A new channel
                matched_ytr_ids.append(ytr_id)
                if ptv_id in ptv_ids:
                    # PTV channel
                    ptv_channel = [ptv_cha for ptv_cha in ptv_channels if ptv_cha.get('id') == ptv_id][0].copy()
                    ptv_channel['ptvId'] = ptv_channel.get('id')
                    ptv_channel['id'] = ytr_id
                    ptv_channel['organizationId'] = channel.get('organizationId')
                    new_channels.append(ptv_channel)
                    matched_ptv_ids.append(ptv_id)
                else:
                    # YTR original channel
                    new_channels.append(channel)

        # Handle rest of thr PTV channels separately
        nonmatched_ptv_ids = list(set(ptv_ids) - set(matched_ptv_ids))
        nonmatched_ptv_channels = [[ptv_channel for ptv_channel in ptv_channels if ptv_channel.get('id') == nonmatched_ptv_id][0] for nonmatched_ptv_id in nonmatched_ptv_ids]
        nonmatched_ptv_channels_mod = []
        for nonmatched_ptv_channel in nonmatched_ptv_channels:
            nonmatched_ptv_channel_c = nonmatched_ptv_channel.copy()
            nonmatched_ptv_channel_c['ptvId'] = nonmatched_ptv_channel_c.get('id')
            nonmatched_ptv_channel_c['organizationId'] = None
            nonmatched_ptv_channels_mod.append(nonmatched_ptv_channel_c)
        return new_channels, nonmatched_ptv_channels_mod, known_channels
    
    def _get_ptv_service_id(self, service: dict) -> list:
        return(service.get('ptvId'))
    
    def _get_ptv_channel_id(self, channel: dict) -> list:
        return(channel.get('ptvId'))
    
    def get_service_types(self) -> list:
        endpoint = "/palvelutyyppi"
        url = API + endpoint
        response = self.api_session.get(url=url)
        return(response.json())
        
    def get_services(self) -> list:
        endpoint = "/palvelu"
        url = API + endpoint
        response = self.api_session.get(url=url)
        
        return(response.json())
        
    def get_service_offers(self) -> list:
        
        try:
            endpoint = "/palvelutarjous"
            url = API + endpoint
            response = self.api_session.get(url=url)
            return(response.json())
        except Exception as e:
            print("There was a problem fetching services from YTR.")
            raise Exception(e)
        
    def get_service_channels(self, channel_ids: list) -> list:
        try:
            channels = []
            for channel_id in channel_ids:
                endpoint = "/palvelukanava/{}".format(channel_id)
                url = API + endpoint
                response = self.api_session.get(url=url)
                channels.append(response.json())
            return(channels)
        except Exception as e:
            print("There was a problem fetching service channels from YTR.")
            raise Exception(e)
        
    def get_organization(self) -> dict:
        endpoint = "/toimija"
        url = API + endpoint
        response = self.api_session.get(url=url)
        
        return(response.json())
        
    def get_municipalities(self) -> list:
        try:
            endpoint = "/kunta"
            url = API + endpoint
            response = self.api_session.get(url=url)
            return(response.json())
        except Exception as e:
            print("There was a problem fetching municipalities from YTR.")
            raise Exception(e)
        

    def update_municipalities_in_mongo(self, municipalities: list, old_municipalities: list) -> None:

        if len(municipalities) > 0:
            old_ids = [municipality.get('id') for municipality in old_municipalities]
            new_ids = [municipality.get('id') for municipality in municipalities]
            removed = list(set(old_ids) - set(new_ids))
            del_count = 0
            delete_result = self.mongo_client.service_db.municipalities.delete_many({'id': {"$in": removed}})
            del_count = delete_result.deleted_count
            print(del_count, "old municipalities deleted.")
            
            added = list(set(new_ids) - set(old_ids))
            municipalities_to_add = [mun for mun in municipalities if mun.get('id') in added]
            self.mongo_client.service_db.municipalities.insert_many(municipalities)
            print(len(municipalities_to_add), "municipalities stored.")
            
    def get_latest_update_time_from_mongo(self, collection: str) -> Optional[datetime]:
        
        if collection == "ytr_services":
            last_result = self.mongo_client.service_db.ytr_services.aggregate([{"$group" : {"_id" : None, "max" : {"$max" : "$lastUpdated"}}}])
            last_result = list(last_result)
            time = None
            if len(last_result) > 0 and last_result[0].get('max') is not None:
                time = datetime.fromtimestamp(last_result[0]['max']/1000)
        elif collection == "ytr_channels":
            last_result = self.mongo_client.service_db.ytr_channels.aggregate([{"$group" : {"_id" : None, "max" : {"$max" : "$lastUpdated"}}}])
            last_result = list(last_result)
            time = None
            if len(last_result) > 0 and last_result[0].get('max') is not None:
                time = datetime.fromtimestamp(last_result[0]['max']/1000)
        else:
            raise Exception("Collection not recognized")
        return(time)
    
    def store_to_mongo(self, collection: str, to_store: list) -> None:
        if collection == "ytr_services":
            if len(to_store) > 0:
                self.mongo_client.service_db.ytr_services.insert_many(to_store)
            print(len(to_store), "new services stored.")
        elif collection == "ytr_channels":
            if len(to_store) > 0:
                self.mongo_client.service_db.ytr_channels.insert_many(to_store)
            print(len(to_store), "new channels stored.")
        else:
            raise Exception("Collection not recognized")

    def remove_old_from_mongo(self) -> None:
        del_count = 0
        delete_result = self.mongo_client.service_db.ytr_services.delete_many({})
        del_count = delete_result.deleted_count
        print(del_count, "old services deleted.")
        del_count = 0
        delete_result = self.mongo_client.service_db.ytr_channels.delete_many({})
        del_count = delete_result.deleted_count
        print(del_count, "old channels deleted.")
    
    def _get_new_services_and_channels(self) -> tuple:
        
        # Get id -> code mapping for YTR municipalities
        municipalities = self.get_municipalities()
        self.municipality_map = self._parse_municipality_map(municipalities)

        # Update service data
        service_offers = self.get_service_offers()
        current_ptv_services = list(self.mongo_client.service_db.services.find({}))
        for current_ptv_service in current_ptv_services:
            if '_id' in current_ptv_service:
                del current_ptv_service['_id']
        service_offers_parsed = [self._parse_service_info(ser) for ser in service_offers]
        ytr_original, ptv_recognized_services = self._filter_and_split_services(service_offers_parsed, current_ptv_services)
        all_services = ptv_recognized_services + ytr_original
        all_services = [ser for ser in all_services if self._is_suitable_service(ser)]
 
        all_channels = []
        all_channel_ids = []
        # Fetch all the channels related to the new and updated services
        for new_service in all_services:
            channels = self.get_service_channels(new_service.get('channelIds'))
            new_service['channelIds'] = [] # Cannot refer to every channel with ID
            channels_parsed = [self._parse_channel_info(cha) for cha in channels]
            channels_parsed_ptv_ids = [cha.get('ptvId') for cha in channels_parsed if cha.get('ptvId') is not None]

            new_service_ptv_id = new_service.get('ptvId')
            if new_service_ptv_id is not None:
                current_ptv_channels_by_service = list(self.mongo_client.service_db.channels.find({'serviceIds': {"$in": [new_service_ptv_id]}}))
                if len(channels_parsed_ptv_ids) > 0:
                    channel_referred_ptv_channels = list(self.mongo_client.service_db.channels.find({'id': {"$in": channels_parsed_ptv_ids}}))
                else:
                    channel_referred_ptv_channels = []
                current_ptv_channels = current_ptv_channels_by_service + channel_referred_ptv_channels
            else:
                current_ptv_channels = []
            for current_ptv_channel in current_ptv_channels:
                current_ptv_channel['serviceIds'] = []
                if '_id' in current_ptv_channel:
                    del current_ptv_channel['_id']

            new_channels, ptv_unrecognized_channels, known_channels = self._split_channels(channels_parsed, all_channels, current_ptv_channels)
            all_new_service_channels = new_channels + ptv_unrecognized_channels
            # Add reference to the services that have been found earlier
            for known_channel in known_channels:
                known_channels_handle = [cha for cha in all_channels if cha.get('ptvId') == known_channel.get('ptvId') or cha.get('id') == known_channel.get('id')][0]
                known_channels_handle['serviceIds'] = known_channels_handle['serviceIds'] + [new_service.get('id')]
            # Add same reference to the new ones
            for channel in all_new_service_channels:
                channel['serviceIds'] = channel['serviceIds'] + [new_service.get('id')]
            all_channels = all_channels + all_new_service_channels
            all_channel_ids = all_channel_ids + [cha.get('id') for cha in all_new_service_channels if cha.get('id') is not None]
        
        return(all_services, all_channels)
        
    def import_ytr_data(self) -> dict:
        all_services, all_channels = self._get_new_services_and_channels()
        
        # If empty response don't update because it's probably some error
        if len(all_services) > 0 and len(all_channels) > 0:
            # Delete all services and channels
            self.remove_old_from_mongo()
            
            # Store original ytr services and matched PTV services to database
            self.store_to_mongo('ytr_services', all_services)
            
            # Store original ytr service channels and those that correspond PTV recognized ones to database
            self.store_to_mongo('ytr_channels', all_channels)
        else:
            print("There was some problem with fetching data from YTR")
        