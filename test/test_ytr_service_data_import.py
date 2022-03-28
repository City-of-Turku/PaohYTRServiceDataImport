import os
import sys
sys.path.append('ytr_service_data_import')
import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from ytr_service_data_importer.ytr_importer import YTRImporter

class YTRServiceDataImporterTest(unittest.TestCase):

    def setUp(self):
        self.municipalities_response = [{'kuntakoodi': '001', 'id': 1,
                                    'nimi': {'sv': 'Åbo', 'fi':'Turku'}},
                                   {'kuntakoodi': '002', 'id': 2,
                                    'nimi': {'sv': 'Nådendal', 'fi':'Naantali'}},
                                   {'kuntakoodi': '003', 'id': 3,
                                    'nimi': {'sv': 'Helsingfors', 'fi':'Helsinki'}}]
        self.ptv_municipalities_response = [{'id': '001',
                                    'name': {'sv': 'Åbo', 'fi':'Turku', 'en': 'Turku'}},
                                   {'id': '002',
                                    'name': {'sv': 'Nådendal', 'fi':'Naantali', 'en':'Naantali'}},
                                   {'id': '003',
                                    'name': {'sv': 'Helsingfors', 'fi':'Helsinki', 'en':'Helsinki'}}]
        
        self.service_offers_response = [{'id': 1,
          'aktiivinen': True,
          'ptvId': '102',            
          'toimija_id': 78,
          'palvelukanavat': [123, 124],
          'nimi': {'fi': 'Aina tuoretta', 'sv': 'Alltid frisk'},
          'kuvaus':  {'fi': '', 'sv': ''},
          'requirements': [],
          'kohderyhmat': [{'koodi': 'KR-4', 'nimi': {'fi': 'Kansalaiset'}}],
          'serviceClasses': [],
          'lifeEvents': [],
          'kuntasaatavuudet': [{'kunta': 1}],
          'muutettu': '2020-12-13T08:02.57.083Z'},
        {'id': 2,
          'aktiivinen': True,
          'ptvId': '103',                 
          'toimija_id': 78,
          'palvelukanavat': [124],
          'nimi': {'fi': 'Aina tuoretta', 'sv': 'Alltid frisk'},
          'kuvaus':  {'fi': '', 'sv': ''},
          'requirements': [],
          'kohderyhmat': [{'koodi': 'KR-4', 'nimi': {'fi': 'Kansalaiset'}}],
          'serviceClasses': [],
          'lifeEvents': [],
          'kuntasaatavuudet': [{'kunta': 1}, {'kunta': 2}],
          'muutettu': '2020-12-13T08:02.57.083Z'},
        {'id': 3,
          'aktiivinen': True,
          'ptvId': None,               
          'toimija_id': 78,
          'palvelukanavat': [125],
          'nimi': {'fi': 'Kotihoiva', 'sv': 'Samma på svenska'},
          'kuvaus':  {'fi': '', 'sv': ''},
          'requirements': [],
          'kohderyhmat': [{'koodi': 'KR-4', 'nimi': {'fi': 'Kansalaiset'}}],
          'serviceClasses': [],
          'lifeEvents': [],
          'kuntasaatavuudet': [{'kunta': 1}, {'kunta': 2}],
          'muutettu': '2020-12-13T08:02.57.083Z'},
        {'id': 4,
          'aktiivinen': True,
          'ptvId': '345',               
          'toimija_id': 78,
          'palvelukanavat': [],
          'nimi': {'fi': 'Kotihoiva', 'sv': 'Samma på svenska'},
          'kuvaus':  {'fi': '', 'sv': ''},
          'requirements': [],
          'kohderyhmat': [{'koodi': 'KR-4', 'nimi': {'fi': 'Kansalaiset'}}],
          'serviceClasses': [],
          'lifeEvents': [],
          'kuntasaatavuudet': [{'kunta': 1}, {'kunta': 2}],
          'muutettu': '2020-12-13T08:02.57.083Z'},
        {'id': 5,
          'aktiivinen': True,
          'ptvId': None,               
          'toimija_id': 78,
          'palvelukanavat': [],
          'nimi': {'fi': 'Kotihoiva', 'sv': 'Samma på svenska'},
          'kuvaus':  {'fi': '', 'sv': ''},
          'requirements': [],
          'kohderyhmat': [{'koodi': 'KR-1', 'nimi': {'fi': 'Ikäihmiset'}}],
          'serviceClasses': [],
          'lifeEvents': [],
          'kuntasaatavuudet': [{'kunta': 1}, {'kunta': 2}],
          'muutettu': '2020-12-13T08:02.57.083Z'}]
        
        self.channels_response = [{'id': 123,
          'aktiivinen': True,              
          'toimija': 78,
          'ptvId': '112',
          'nimi': {'fi': 'Aina tuoretta', 'sv': 'Alltid frisk'},
          'kuvaus':  {'fi': 'Kuvaus', 'sv': 'På svenska'},
          'osoite': {'id': 2,
            'katuosoite': {'fi': 'Rauhankatu 14 B'},
            'postinumero': '20100',
            'kunta': 1},
          'yhteystiedot': [{'id': 1,
            'yhteystietotyyppi': {'id': 2,
              'nimet': {'fi': 'Verkkosivun osoite', 'sv': 'Webbsida'}},
            'arvo': 'https://www.jokinurli.fi',
            'lisatieto': {},
            'palvelukanava': 123},
            {'id': 65,
            'yhteystietotyyppi': {'id': 1,
            'nimet': {'fi': 'Puhelinnumero', 'sv': 'Telefon'}},
            'arvo': '040 1234567',
               'lisatieto': {},
               'palvelukanava': 123}],
          'muutettu': '2020-12-13T08:02.57.083Z'},
        {'id': 124,
          'aktiivinen': True, 
          'ptvId': '113',           
          'toimija': 78,
          'nimi': {'fi': 'Aina tuoretta2', 'sv': 'Alltid frisk2'},
          'kuvaus':  {'fi': 'Kuvaus', 'sv': 'På svenska'},
          'osoite': {'id': 2,
            'katuosoite': {'fi': 'Rauhankatu 14 B'},
            'postinumero': '20100',
            'kunta': 1},
          'yhteystiedot': [{'id': 1,
            'yhteystietotyyppi': {'id': 2,
              'nimet': {'fi': 'Verkkosivun osoite', 'sv': 'Webbsida'}},
            'arvo': 'https://www.jokinurli.fi',
            'lisatieto': {},
            'palvelukanava': 124},
            {'id': 65,
            'yhteystietotyyppi': {'id': 1,
            'nimet': {'fi': 'Puhelinnumero', 'sv': 'Telefon'}},
            'arvo': '040 1234567',
               'lisatieto': {},
               'palvelukanava': 124}],
          'muutettu': '2020-12-13T08:02.57.083Z'},
        {'id': 125,
          'aktiivinen': True,
          'ptvId': None,              
          'toimija': 78,
          'nimi': {'fi': 'Aina tuoretta3', 'sv': 'Alltid frisk3'},
          'kuvaus':  {'fi': 'Kuvaus', 'sv': 'På svenska'},
          'osoite': {'id': 2,
            'katuosoite': {'fi': 'Rauhankatu 14 B'},
            'postinumero': '20100',
            'kunta': 1},
          'yhteystiedot': [{'id': 1,
            'yhteystietotyyppi': {'id': 2,
              'nimet': {'fi': 'Verkkosivun osoite', 'sv': 'Webbsida'}},
            'arvo': 'https://www.jokinurli.fi',
            'lisatieto': {},
            'palvelukanava': 125},
            {'id': 65,
            'yhteystietotyyppi': {'id': 1,
            'nimet': {'fi': 'Puhelinnumero', 'sv': 'Telefon'}},
            'arvo': '040 1234567',
               'lisatieto': {},
               'palvelukanava': 125}],
          'muutettu': '2020-12-13T08:02.57.083Z'}]
        self.channels_response1 = self.channels_response[0]
        self.channels_response2 = self.channels_response[1]        
        self.channels_response3 = self.channels_response[1]
        self.channels_response4 = self.channels_response[2]
        
        
        # PTV services
        self.ptv_services_response = [{"id":"102",
        "type":"Service",
        "subtype":None,
        "channelIds":["112","113"],
        "organizations":[{"id":"d06969b2-342b-4063-bfc8-6372e2545d81","name":"Digi- ja väestötietovirasto"},{"id":"d06969b2-342b-4063-bfc8-6372e2545d81","name":"Digi- ja väestötietovirasto"}],
        "name":{"en":None,"fi":"Aina tuoretta","sv":"Alltid frisk"},
        "descriptions":{"en":[],"fi":[],"sv":[]},
        "requirement":{"en":"","fi":"","sv":""},
        "targetGroups":{"en":[],"fi":[{"name":"Kansalaiset","code":"KR1"}],"sv":[]},
        "serviceClasses":{"en":[],"fi":[],"sv":[]},
        "areas":{"en":[],"fi":[],"sv":[]},
        "lifeEvents":{"en":[],"fi":[],"sv":[]},
        "lastUpdated":datetime.strptime("2021-08-06T08:26:31.495Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        {"id":"103",
        "type":"Service",
        "subtype":None,
        "channelIds":["113","114"],
        "organizations":[{"id":"d06969b2-342b-4063-bfc8-6372e2545d81","name":"Digi- ja väestötietovirasto"},{"id":"d06969b2-342b-4063-bfc8-6372e2545d81","name":"Digi- ja väestötietovirasto"}],
        "name":{"en":None,"fi":"Aina tuoretta","sv":"Alltid frisk"},
        "descriptions":{"en":[],"fi":[],"sv":[]},
        "requirement":{"en":"","fi":"","sv":""},
        "targetGroups":{"en":[],"fi":[{"name":"Kansalaiset","code":"KR1"}],"sv":[]},
        "serviceClasses":{"en":[],"fi":[],"sv":[]},
        "areas":{"en":[],"fi":[],"sv":[]},
        "lifeEvents":{"en":[],"fi":[],"sv":[]},
        "lastUpdated":datetime.strptime("2021-08-06T08:26:31.495Z", "%Y-%m-%dT%H:%M:%S.%fZ")}]
        
        # PTV channels
        self.ptv_channels_response = [{"id":"112",
        "type":"EChannel",
        "areaType":"Nationwide",
        "organizationId":"2c228180-75cd-4ee3-853c-3ca3ae8c54a2",
        "serviceIds":["101"],
        "name":{"en":"Always fresh","fi":"Aina tuoretta","sv":"Alltid frisk"},
        "descriptions":{"en":[{"value":"In English","type":"Summary"}],"fi":[{"value":"Kuvaus","type":"Summary"}],"sv":[{"value":"På svenska","type":"Summary"}]},
        "webPages":{"en":[],"fi":[],"sv":[]},
        "emails":{"en":[],"fi":[],"sv":[]},
        "phoneNumbers":{"en":[],"fi":[],"sv":[]},
        "addresses":{"en":[],"fi":[],"sv":[]},
        "areas":{"en":[],"fi":[],"sv":[]},
        "lastUpdated":datetime.strptime("2021-08-06T08:26:31.495Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        {"id":"113",
        "type":"EChannel",
        "areaType":"Nationwide",
        "organizationId":"2c228180-75cd-4ee3-853c-3ca3ae8c54a2",
        "serviceIds":["101"],
        "name":{"en":"Always fresh","fi":"Aina tuoretta","sv":"Alltid frisk"},
        "descriptions":{"en":[{"value":"In English","type":"Summary"}],"fi":[{"value":"Kuvaus","type":"Summary"}],"sv":[{"value":"På svenska","type":"Summary"}]},
        "webPages":{"en":[],"fi":[],"sv":[]},
        "emails":{"en":[],"fi":[],"sv":[]},
        "phoneNumbers":{"en":[],"fi":[],"sv":[]},
        "addresses":{"en":[],"fi":[],"sv":[]},
        "areas":{"en":[],"fi":[],"sv":[]},
        "lastUpdated":datetime.strptime("2021-08-06T08:26:31.495Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        {"id":"114",
        "type":"EChannel",
        "areaType":"Nationwide",
        "organizationId":"2c228180-75cd-4ee3-853c-3ca3ae8c54a2",
        "serviceIds":["103"],
        "name":{"en":"Always fresh","fi":"Aina tuoretta","sv":"Alltid frisk"},
        "descriptions":{"en":[{"value":"In English","type":"Summary"}],"fi":[{"value":"Kuvaus","type":"Summary"}],"sv":[{"value":"På svenska","type":"Summary"}]},
        "webPages":{"en":[],"fi":[],"sv":[]},
        "emails":{"en":[],"fi":[],"sv":[]},
        "phoneNumbers":{"en":[],"fi":[],"sv":[]},
        "addresses":{"en":[],"fi":[],"sv":[]},
        "areas":{"en":[],"fi":[],"sv":[]},
        "lastUpdated":datetime.strptime("2021-08-06T08:26:31.495Z", "%Y-%m-%dT%H:%M:%S.%fZ")}]
        self.ptv_channels_response1 = self.ptv_channels_response[0:2]
        self.ptv_channels_response2 = self.ptv_channels_response[0:2]
        self.ptv_channels_response3 = self.ptv_channels_response[1:3]
        self.ptv_channels_response4 = self.ptv_channels_response[1:3]
        self.ptv_channels_response5 = []
        self.ptv_channels_response6 = []
        self.ptv_channels_response7 = []
        self.ptv_channels_response8 = []
        self.mongo_response = [{'_id': None,'max': 1000 * datetime.strptime('2020-12-11T08:02.57.083Z', "%Y-%m-%dT%H:%M.%S.%fZ").timestamp()}]

        # PTV municipalities
        self.mongo_client_instance = MagicMock()
        self.mongo_client_instance.service_db = MagicMock()        
        self.mongo_client_instance.service_db.municipalities = MagicMock()
        self.mongo_client_instance.service_db.municipalities.find = MagicMock()
        self.mongo_client_instance.service_db.municipalities.find.return_value = self.ptv_municipalities_response
        # PTV services
        self.mongo_client_instance.service_db.services = MagicMock()
        self.mongo_client_instance.service_db.services.find = MagicMock()
        self.mongo_client_instance.service_db.services.find.return_value = self.ptv_services_response
        
        # PTV channels
        self.mongo_client_instance.service_db.channels = MagicMock()
        self.mongo_client_instance.service_db.channels.find = MagicMock()
        self.mongo_client_instance.service_db.channels.find.side_effect = [self.ptv_channels_response1, self.ptv_channels_response2, self.ptv_channels_response3, self.ptv_channels_response4, self.ptv_channels_response5, self.ptv_channels_response6, self.ptv_channels_response7, self.ptv_channels_response8]

        # Current YTR services
        self.mongo_client_instance.service_db.ytr_services = MagicMock()
        self.mongo_client_instance.service_db.ytr_services.aggregate = MagicMock()
        self.mongo_client_instance.service_db.ytr_services.aggregate.return_value = self.mongo_response

        # YTR requests
        self.api_session_instance = MagicMock()
        self.api_session_instance.get = MagicMock()
        get_mock_0 = MagicMock()
        get_mock_0.json = MagicMock()
        get_mock_0.json.return_value = self.municipalities_response
        get_mock_1 = MagicMock()
        get_mock_1.json = MagicMock()
        get_mock_1.json.return_value = self.service_offers_response
        get_mock_2 = MagicMock()
        get_mock_2.json = MagicMock()
        get_mock_2.json.return_value = self.channels_response1
        get_mock_3 = MagicMock()
        get_mock_3.json = MagicMock()
        get_mock_3.json.return_value = self.channels_response2
        get_mock_4 = MagicMock()
        get_mock_4.json = MagicMock()
        get_mock_4.json.return_value = self.channels_response3
        get_mock_5 = MagicMock()
        get_mock_5.json = MagicMock()
        get_mock_5.json.return_value = self.channels_response4
        self.api_session_instance.get.side_effect = [get_mock_0, get_mock_1, get_mock_2, get_mock_3, get_mock_4, get_mock_5]
        
        self.ytr_importer = YTRImporter(self.mongo_client_instance, self.api_session_instance)

    def test_latest_update_time(self):
        lu_time = self.ytr_importer.get_latest_update_time_from_mongo('ytr_services')
        self.assertEqual(lu_time, datetime(2020, 12, 11, 8, 2, 57, 83000))

    def test_parse_municipality_map(self):
        self.setUp()
        municipalities = self.ytr_importer.get_municipalities()
        self.ytr_importer.municipality_map = self.ytr_importer._parse_municipality_map(municipalities)
        self.assertEqual(self.ytr_importer.municipality_map.get(2), '002')        
        
    def test_parse_service_info(self):
        self.setUp()
        municipalities = self.ytr_importer.get_municipalities()
        self.ytr_importer.municipality_map = self.ytr_importer._parse_municipality_map(municipalities)
        
        # Parse service
        service_orig = self.service_offers_response[0]
        service_parsed = self.ytr_importer._parse_service_info(service_orig)
        self.assertEqual(service_parsed['organizations'][0]['id'], str(service_orig['toimija_id']))
        self.assertEqual(service_parsed['name']['fi'], service_orig['nimi']['fi'])
        self.assertEqual(service_parsed['targetGroups']['fi'][0]['name'], service_orig['kohderyhmat'][0]['nimi']['fi'])
        self.assertEqual(service_parsed['areas']['fi'][0]['name'], 'Turku')
        self.assertEqual(len(service_parsed['channelIds']), 2)  
        self.assertEqual(service_parsed['lastUpdated'], datetime(2020, 12, 13, 8, 2, 57, 83000)) 
        
    def test_parse_channel_info(self):
        self.setUp()
        municipalities = self.ytr_importer.get_municipalities()
        self.ytr_importer.municipality_map = self.ytr_importer._parse_municipality_map(municipalities)
        
        # Parse channel
        channel_orig = self.channels_response[0]
        channel_parsed = self.ytr_importer._parse_channel_info(channel_orig)
        self.assertEqual(channel_parsed['organizationId'], str(channel_orig['toimija']))
        self.assertEqual(channel_parsed['name']['fi'], channel_orig['nimi']['fi'])
        self.assertEqual(channel_parsed['descriptions']['fi'][0]['value'], channel_orig['kuvaus']['fi'])
        self.assertEqual(channel_parsed['webPages']['fi'][0], channel_orig['yhteystiedot'][0]['arvo'])
        self.assertEqual(channel_parsed['addresses']['fi'][0]['municipalityName'], 'Turku')
        self.assertEqual(len(channel_parsed['serviceIds']), 0)
        self.assertEqual(channel_parsed['lastUpdated'], datetime(2020, 12, 13, 8, 2, 57, 83000))  
        
    def test_get_new_services_and_channels(self):
        self.setUp()
        municipalities = self.ytr_importer.get_municipalities()
        self.ytr_importer.municipality_map = self.ytr_importer._parse_municipality_map(municipalities)

        # Services
        service_offers = self.ytr_importer.get_service_offers()
        service_offers_parsed = [self.ytr_importer._parse_service_info(ser) for ser in service_offers]
        self.assertEqual(len(service_offers_parsed), 5)
        service_offers_parsed = [ser for ser in service_offers_parsed if self.ytr_importer._is_suitable_service(ser)]
        self.assertEqual(len(service_offers_parsed), 4)
        last_update_time = self.ytr_importer.get_latest_update_time_from_mongo('ytr_services')
        service_offers_new = [so for so in service_offers_parsed if last_update_time is None or so.get('lastUpdated') is None or so.get('lastUpdated') > last_update_time]
        self.assertEqual(len(service_offers_new), 4)
        ytr_original, ptv_recognized_services = self.ytr_importer._filter_and_split_services(service_offers_new, self.ptv_services_response)
        self.assertEqual(len(ytr_original), 2)
        self.assertEqual(len(ptv_recognized_services), 2)
        
        # Channels
        all_channel_ids = []
        all_channels = []
        new_service = ptv_recognized_services[0]
        channels = self.ytr_importer.get_service_channels(new_service.get('channelIds'))
        channels_parsed = [self.ytr_importer._parse_channel_info(cha) for cha in channels]
        channels_parsed_ptv_ids = [cha.get('ptvId') for cha in channels_parsed if cha.get('ptvId') is not None]
            
        new_service_ptv_id = new_service.get('ptvId')
        if new_service_ptv_id is not None:
            current_ptv_channels_by_service = list(self.ytr_importer.mongo_client.service_db.channels.find({'serviceIds': {"$in": [new_service_ptv_id]}}))
            if len(channels_parsed_ptv_ids) > 0:
                channel_referred_ptv_channels = list(self.ytr_importer.mongo_client.service_db.channels.find({'id': {"$in": channels_parsed_ptv_ids}}))
            else:
                channel_referred_ptv_channels = []
            current_ptv_channels = current_ptv_channels_by_service + channel_referred_ptv_channels
        else:
            current_ptv_channels = []
        new_channels, ptv_unrecognized_channels, known_channels = self.ytr_importer._split_channels(channels_parsed, all_channels, current_ptv_channels)
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
    
        self.assertEqual(len(new_channels), 2)
        self.assertEqual(len(ptv_unrecognized_channels), 0)
        self.assertEqual(len(known_channels), 0)
        
        new_service = ptv_recognized_services[1]
        channels = self.ytr_importer.get_service_channels(new_service.get('channelIds'))
        channels_parsed = [self.ytr_importer._parse_channel_info(cha) for cha in channels]
        channels_parsed_ptv_ids = [cha.get('ptvId') for cha in channels_parsed if cha.get('ptvId') is not None]

        new_service_ptv_id = new_service.get('ptvId')
        if new_service_ptv_id is not None:
            current_ptv_channels_by_service = list(self.ytr_importer.mongo_client.service_db.channels.find({'serviceIds': {"$in": [new_service_ptv_id]}}))
            if len(channels_parsed_ptv_ids) > 0:
                channel_referred_ptv_channels = list(self.ytr_importer.mongo_client.service_db.channels.find({'id': {"$in": channels_parsed_ptv_ids}}))
            else:
                channel_referred_ptv_channels = []
            current_ptv_channels = current_ptv_channels_by_service + channel_referred_ptv_channels
        else:
            current_ptv_channels = []
        new_channels, ptv_unrecognized_channels, known_channels = self.ytr_importer._split_channels(channels_parsed, all_channels, current_ptv_channels)
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
        
        self.assertEqual(len(new_channels), 0)
        self.assertEqual(len(ptv_unrecognized_channels), 1)
        self.assertEqual(len(known_channels), 1)
        
        new_service = ytr_original[0]
        channels = self.ytr_importer.get_service_channels(new_service.get('channelIds'))
        channels_parsed = [self.ytr_importer._parse_channel_info(cha) for cha in channels]
        channels_parsed_ptv_ids = [cha.get('ptvId') for cha in channels_parsed if cha.get('ptvId') is not None] 

        new_service_ptv_id = new_service.get('ptvId')
        if new_service_ptv_id is not None:
            current_ptv_channels_by_service = list(self.ytr_importer.mongo_client.service_db.channels.find({'serviceIds': {"$in": [new_service_ptv_id]}}))
            if len(channels_parsed_ptv_ids) > 0:
                channel_referred_ptv_channels = list(self.ytr_importer.mongo_client.service_db.channels.find({'id': {"$in": channels_parsed_ptv_ids}}))
            else:
                channel_referred_ptv_channels = []
            current_ptv_channels = current_ptv_channels_by_service + channel_referred_ptv_channels
        else:
            current_ptv_channels = []
        new_channels, ptv_unrecognized_channels, known_channels = self.ytr_importer._split_channels(channels_parsed, all_channels, current_ptv_channels)
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
        
        self.assertEqual(len(new_channels), 1)
        self.assertEqual(len(ptv_unrecognized_channels), 0)
        self.assertEqual(len(known_channels), 0)

    def test_import_ytr_data(self):
        self.setUp()
        all_services, all_channels = self.ytr_importer._get_new_services_and_channels()
        self.assertEqual(len(all_services), 4)
        self.assertEqual(len(all_channels), 4)

if __name__ == '__main__':
    unittest.main()
