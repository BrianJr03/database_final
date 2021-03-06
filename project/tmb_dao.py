import unittest
import json
from datetime import datetime, timedelta
import sys, re
from mysqlutils import SQL_runner

class TMB_DAO:

    def __init__(self, stub=False):
        self.is_stub = stub    

    def insert_message_batch(self, batch):
        """
        Insert a batch of messages

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: Number of successful insertions
        :rtype: int
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return len(array)

        pos_insertions = 0
        static_insertions = 0
        ais_msg_insertions = 0    

        for ais_msg in array:

            date_time_obj = datetime.strptime(ais_msg["Timestamp"], '%Y-%m-%dT%H:%M:%S.%fZ')

            QUERY1=f"""
            SELECT Id FROM AIS_MESSAGE  
            ORDER BY Id DESC  
            LIMIT 1;
            """
            rs = SQL_runner().run(QUERY1)
            id = rs[0][0]
            id += 1

            QUERY2=f"""
            INSERT INTO AIS_MESSAGE 
            (Id, Timestamp, MMSI, Class) 
            VALUES (
            {id},
            '{date_time_obj}', 
            '{ais_msg["MMSI"]}', 
            '{ais_msg["Class"]}');
            SELECT ROW_COUNT();
            """
            rs = SQL_runner().run(QUERY2)
            ais_msg_insertions += rs[0][0]

            if ais_msg["MsgType"] == "static_data":

                QUERY3=f"""
                INSERT INTO STATIC_DATA 
                (AIS_IMO, Name, VesselType, Length, Breadth) 
                VALUES (
                '{ais_msg["IMO"] if type(ais_msg["IMO"]) is int else 1}', 
                '{ais_msg["Name"]}', 
                '{ais_msg["VesselType"]}', 
                {ais_msg["Length"]}, 
                {ais_msg["Breadth"]}); 
                SELECT ROW_COUNT();
                """
                rs = SQL_runner().run(QUERY3)
                static_insertions += rs[0][0]

            if ais_msg["MsgType"] == "position_report":
                
                if "RoT" not in ais_msg:
                    ais_msg["RoT"] = 0 

                QUERY4=f"""
                INSERT INTO POSITION_REPORT 
                (AISMessage_Id, NavigationalStatus, Longitude, Latitude, RoT, SoG, CoG, Heading) 
                VALUES (
                5,
                '{ais_msg["Status"]}', 
                {ais_msg["Position"]["coordinates"][1]}, 
                {ais_msg["Position"]["coordinates"][0]}, 
                {ais_msg["RoT"]}, 
                {ais_msg["SoG"]}, 
                {ais_msg["CoG"]}, 
                {ais_msg["Heading"]}); 
                SELECT ROW_COUNT();
                """
                rs = SQL_runner().run(QUERY4)
                pos_insertions += rs[0][0]

        print(f"\nAIS Message Insertions: {ais_msg_insertions}")
        print(f"Static Data Insertions: {static_insertions}")
        print(f"Position Report Insertions: {pos_insertions}")        
        print(f"Total Insertion Count: {pos_insertions + static_insertions + ais_msg_insertions}")
        return pos_insertions + static_insertions + ais_msg_insertions    

            

    def insert_message(self, batch):
        """
        Insert an AIS message
        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: completion code number
        :rtype: int
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return len(array)

        insertions = 0

        for ais_msg in array:
            if ais_msg["MsgType"] == "static_data":
                QUERY = f"""
                        INSERT INTO STATIC_DATA 
                        (AIS_IMO, Name, VesselType, Length, Breadth) 
                        VALUES (
                        '{ais_msg["IMO"] if type(ais_msg["IMO"]) is int else 1}', 
                        '{ais_msg["Name"]}', 
                        '{ais_msg["VesselType"]}', 
                        {ais_msg["Length"]}, 
                        {ais_msg["Breadth"]}); 
                        SELECT ROW_COUNT();
                        """
                rs = SQL_runner().run(QUERY)
                insertions += rs[0][0]

            if ais_msg["MsgType"] == "position_report":

                if "RoT" not in ais_msg:
                    ais_msg["RoT"] = 0

                QUERY = f"""
                        INSERT INTO POSITION_REPORT 
                        (AISMessage_Id, NavigationalStatus, Longitude, Latitude, RoT, SoG, CoG, Heading) 
                        VALUES (
                        5,
                        '{ais_msg["Status"]}', 
                        {ais_msg["Position"]["coordinates"][1]}, 
                        {ais_msg["Position"]["coordinates"][0]}, 
                        {ais_msg["RoT"]}, 
                        {ais_msg["SoG"]}, 
                        {ais_msg["CoG"]}, 
                        {ais_msg["Heading"]}); 
                        SELECT ROW_COUNT();
                        """
                rs = SQL_runner().run(QUERY)
                insertions += rs[0][0]

        return insertions        

    def delete_all_msg_timestamp(self, batch):
        """
        Delete all AIS Messages older than 5 minutes

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: Number of successful deletions
        :rtype: int
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
           len(array)

        deletions = 0
        for ais_msg in array:
            now = datetime.now()
            timestamp = ais_msg["Timestamp"]
            date_time_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')

            if now - date_time_obj > timedelta(minutes=5):
                QUERY = f"""
                delete AIS_MESSAGE, POSITION_REPORT, STATIC_DATA 
                from AIS_MESSAGE 
                LEFT join POSITION_REPORT on AIS_MESSAGE.Id = POSITION_REPORT.AISMessage_Id 
                LEFT join STATIC_DATA on AIS_MESSAGE.Id = STATIC_DATA.AISMessage_Id 
                WHERE Timestamp = '{date_time_obj}' AND POSITION_REPORT.LastStaticData_Id = STATIC_DATA.DestinationPort_Id ;
                SELECT ROW_COUNT();
                """
                rs = SQL_runner().run(QUERY)
                deletions += rs[0][0]
        return deletions   

    def read_most_recent_ship_pos(self, batch):
        """
        Read all most recent ship positions

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: list of ship documents
        :rtype: list
        """
        if batch == "" or batch == None:
            return -1 

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array

        QUERY="""
            SELECT MMSI, Latitude, Longitude, AIS_MESSAGE.Vessel_IMO FROM POSITION_REPORT, AIS_MESSAGE, 
            (SELECT max(Timestamp) as time, Vessel_IMO from AIS_MESSAGE GROUP BY Vessel_IMO) 
            RECENT_SHIP WHERE POSITION_REPORT.AISMessage_Id = AIS_MESSAGE.Id AND AIS_MESSAGE.Vessel_IMO = RECENT_SHIP.Vessel_IMO;
            """
        rs = SQL_runner().run(QUERY)
        return rs

    def read_pos_MMSI(self, batch):
        """
        Read most recent position of given MMSI

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: a single position document
        :rtype: dict
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
           return array[0]

        mmsi = input("Please enter an MMSI to query the most recent position: ")

        try:
            int(mmsi)
        except ValueError:
            print("Value must be an integer.")
            return - 1

        QUERY = f"""SELECT MMSI, Latitude, Longitude, Vessel_IMO 
        FROM POSITION_REPORT, AIS_MESSAGE WHERE MMSI = {mmsi} AND POSITION_REPORT.AISMessage_Id = AIS_MESSAGE.Id 
        ORDER BY Timestamp LIMIT 1;"""
        rs = SQL_runner().run(QUERY)
        return rs[0]   

    def read_vessel_info(self, batch):
        """
        Read permanent or transient vessel information matching the given MMSI,
        and 0 or more additional criteria: IMO, Name, CallSign

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: a single vessel document
        :rtype: dict
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array[0]

        mmsi = input("Please enter an MMSI to read permanent or transient vessel information matching the given MMSI: ")

        QUERY = f"""SELECT MMSI, Latitude, Longitude, AIS_MESSAGE.Vessel_IMO, CallSign 
        FROM POSITION_REPORT, AIS_MESSAGE, STATIC_DATA 
        WHERE AIS_MESSAGE.Id = POSITION_REPORT.AISMessage_Id 
        AND AIS_MESSAGE.Id = STATIC_DATA.AISMessage_Id 
        AND POSITION_REPORT.LastStaticData_Id = STATIC_DATA.DestinationPort_Id AND MMSI = {mmsi};"""
        rs = SQL_runner().run(QUERY)
        return rs[0]     

    def read_most_recent_ship_pos_in_tile(self, batch):
        """
        Read all most recent ship positions in the given tile

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: list of ship documents
        :rtype: list
        """
        if batch == "" or batch == None:
            return -1 

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array

        tile_id = input("Please eneter a tile id to search: ") 
           
        try:
            int(tile_id)
        except ValueError:
            print("Value must be an integer.")
            return - 1  

        QUERY=f"""
        SELECT MMSI, Latitude, Longitude, AIS_MESSAGE.Vessel_IMO FROM POSITION_REPORT, AIS_MESSAGE, MAP_VIEW,
        (SELECT max(Timestamp) as time, Vessel_IMO from AIS_MESSAGE GROUP BY Vessel_IMO) 
        RECENT_SHIP WHERE POSITION_REPORT.AISMessage_Id = AIS_MESSAGE.Id AND AIS_MESSAGE.Vessel_IMO = RECENT_SHIP.Vessel_IMO
        AND MAP_VIEW.Id = {tile_id};
        """
        rs = SQL_runner().run(QUERY)
        return rs        

    def read_all_ports(self, batch):
        """
        Read all ports matching the given name and (optional) country

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: list of Port documents
        :rtype: list
        """
        if batch == "" or batch == None:
            return -1 

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array

        print("Please provide the following info to read all matching ports")
        name = input("Enter the Port's name")
        country = input("Enter the country the Port is located in: ")

        QUERY = f"""
        SELECT * FROM PORT WHERE Name = '{name}' and Country = '{country}';
        """

        rs = SQL_runner().run(QUERY)
        return rs


    def read_all_ship_pos_scale3(self, batch):
        """
        Read all ship positions in the tile of scale 3 containing the given port

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: list of (Port or Position) documents 
        :rtype: list
        """
        if batch == "" or batch == None:
            return -1 

        try:
            array = json.loads(batch)
        except Exception:
            return -1   

        if self.is_stub:
            return array

        print("Please provide the following info to read all ship positions in the tile of scale 3")
        name = input("Enter the Port's name: ")
        country = input("Enter the country the Port is located in: ") 

        QUERY=f"""
        Select Longitude, Latitude, Scale FROM PORT, MAP_VIEW
        WHERE Scale = 3 AND Port.Name = '{name}' AND Port.Country = '{country}';
        """
        rs = SQL_runner().run(QUERY)
        return rs     

    def read_last_5_pos(self, batch):
        """
        Read last 5 positions of given MMSI

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: a single document 
        :rtype: dict
        """
        if batch == "" or batch == None:
            return -1 

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array

        mmsi = input("Please enter an MMSI to query the last 5 positions: ")

        try:
            int(mmsi)
        except ValueError:
            print("Value must be an integer.")
            return - 1

        QUERY = f"""SELECT MMSI, Latitude, Longitude, Vessel_IMO 
        FROM POSITION_REPORT, AIS_MESSAGE WHERE MMSI = {mmsi} AND POSITION_REPORT.AISMessage_Id = AIS_MESSAGE.Id 
        ORDER BY Timestamp DESC LIMIT 5;"""
        rs = SQL_runner().run(QUERY)
        return rs    

    def read_position_to_port_id(self, batch):
        """
        Read most recent positions of ships headed to port with given ID

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: a list of position documents
        :rtype: list
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array

        given_id = input("Please enter a Port Id to read most recent positions of ships headed to the port: ")

        QUERY = f"""
        SELECT MMSI, Latitude, Longitude, Vessel_IMO FROM POSITION_REPORT, AIS_MESSAGE 
        WHERE AIS_MESSAGE.Id = {given_id} AND POSITION_REPORT.AISMessage_Id = AIS_MESSAGE.Id;
        """
        rs = SQL_runner().run(QUERY)    

        return -1

    def read_position_given_port(self, batch):
        """
        Read most recent positions of ships headed to given port

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: a list of position documents or array of port documents
        :rtype: list
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array

        port_id = input("Please enter a Port Id to read most recent positions of ships headed to given the Port: ")    

        QUERY=f"""SELECT MMSI, Latitude, Longitude, AIS_MESSAGE.Vessel_IMO FROM POSITION_REPORT, AIS_MESSAGE, PORT, 
        (SELECT max(Timestamp) as time, Vessel_IMO from AIS_MESSAGE GROUP BY Vessel_IMO) RECENT_SHIP 
        WHERE POSITION_REPORT.AISMessage_Id = AIS_MESSAGE.Id AND AIS_MESSAGE.Vessel_IMO = RECENT_SHIP.Vessel_IMO 
        AND PORT.Id = {port_id} AND POSITION_REPORT.MapView1_Id = PORT.MapView1_Id 
        AND POSITION_REPORT.MapView2_Id = PORT.MapView2_Id AND POSITION_REPORT.MapView3_Id = PORT.MapView3_Id;
        """
        rs = SQL_runner().run(QUERY)  
        return rs

    def find_tiles_zoom_2(self, batch):
        """
        Given a background map tile for zoom level 1 (2), find the 4 tiles of zoom level 2 (3) that are contained in it

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: a list of map tile description documents
        :rtype: list
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return array

        return -1

    def find_tile_from_id(self, batch):
        """
        Given a tile ID, get the actual tile (a PNG file)

        :param: batch: a string that represent a JSON array of docs
        :type: batch: str
        :return: a PNG file
        :rtype: binary data
        """
        if batch == "" or batch == None:
            return -1

        try:
            array = json.loads(batch)
        except Exception:
            return -1

        if self.is_stub:
            return bytes(1)

        id = input("Please enter a tile ID to get the actual tile: ")

        try:
            int(id)
        except ValueError:
            print("Value must be an integer.")
            return - 1 

        QUERY = f"""
        SELECT RasterFile FROM MAP_VIEW WHERE Id={id};
        """
        rs = SQL_runner().run(QUERY)
        return rs


class TMBTest(unittest.TestCase):
    batch = """[ {\"Timestamp\":\"2020-11-18T00:00:00.000Z\",\"Class\":\"Class A\",\"MMSI\":304858000,\"MsgType\":\"position_report\",\"Position\":{\"type\":\"Point\",\"coordinates\":[55.218332,13.371672]},\"Status\":\"Under way using engine\",\"SoG\":10.8,\"CoG\":94.3,\"Heading\":97},
                {\"Timestamp\":\"2020-11-19T00:00:00.000Z\",\"Class\":\"AtoN\",\"MMSI\":992111840,\"MsgType\":\"static_data\",\"IMO\":\"Unknown\",\"Name\":\"WIND FARM BALTIC1NW\",\"VesselType\":\"Undefined\",\"Length\":60,\"Breadth\":60,\"A\":30,\"B\":30,\"C\":30,\"D\":30},
                {\"Timestamp\":\"2020-11-20T00:00:00.000Z\",\"Class\":\"Class A\",\"MMSI\":219005465,\"MsgType\":\"position_report\",\"Position\":{\"type\":\"Point\",\"coordinates\":[54.572602,11.929218]},\"Status\":\"Under way using engine\",\"RoT\":0,\"SoG\":0,\"CoG\":298.7,\"Heading\":203},
                {\"Timestamp\":\"2020-11-21T00:00:00.000Z\",\"Class\":\"Class A\",\"MMSI\":257961000,\"MsgType\":\"position_report\",\"Position\":{\"type\":\"Point\",\"coordinates\":[55.00316,12.809015]},\"Status\":\"Under way using engine\",\"RoT\":0,\"SoG\":0.2,\"CoG\":225.6,\"Heading\":240},
                {\"Timestamp\":\"2020-11-18T00:00:00.000Z\",\"Class\":\"AtoN\",\"MMSI\":992111923,\"MsgType\":\"static_data\",\"IMO\":\"Unknown\",\"Name\":\"BALTIC2 WINDFARM SW\",\"VesselType\":\"Undefined\",\"Length\":8,\"Breadth\":12,\"A\":4,\"B\":4,\"C\":4,\"D\":8},
                {\"Timestamp\":\"2020-11-18T00:00:00.000Z\",\"Class\":\"Class A\",\"MMSI\":257385000,\"MsgType\":\"position_report\",\"Position\":{\"type\":\"Point\",\"coordinates\":[55.219403,13.127725]},\"Status\":\"Under way using engine\",\"RoT\":25.7,\"SoG\":12.3,\"CoG\":96.5,\"Heading\":101},
                {\"Timestamp\":\"2020-11-18T00:00:00.000Z\",\"Class\":\"Class A\",\"MMSI\":376503000,\"MsgType\":\"position_report\",\"Position\":{\"type\":\"Point\",\"coordinates\":[54.519373,11.47914]},\"Status\":\"Under way using engine\",\"RoT\":0,\"SoG\":7.6,\"CoG\":294.4,\"Heading\":290} ]"""

    def test_insert_message_batch_interface_1(self):
        """
        Function `insert_message_batch` takes a JSON parsable string as an input.
        Returns: number (int) of insertions
        """
        tmb = TMB_DAO(True) 
        inserted_count = tmb.insert_message_batch(self.batch)
        self.assertTrue(type(inserted_count) is int and inserted_count >=0)

    def test_insert_message_batch_interface_2(self):
        """
        Function `insert_message_batch` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        inserted_count = tmb.insert_message_batch(array)
        self.assertEqual(inserted_count, -1)  

    def test_insert_message_interface_1(self):
        """
        Function `insert_message` takes a JSON parsable string as an input.
        Returns: completion code number
        """
        tmb = TMB_DAO(True) 
        success_code_num = tmb.insert_message(self.batch)
        self.assertTrue(type(success_code_num) is int)

    def test_insert_message_interface_2(self):
        """
        Function `insert_message_batch` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        success_code_num = tmb.insert_message(array)
        self.assertEqual(success_code_num, -1)

    def test_delete_all_msg_timestamp_1(self):
        """
        Function `delete_all_msg_timestamp` takes a JSON parsable string as an input.
        Returns: number (int) of deletions
        """
        tmb = TMB_DAO(True)
        deletion_count = tmb.delete_all_msg_timestamp(self.batch)
        self.assertTrue(type(deletion_count) is int)

    def test_delete_all_msg_timestamp_2(self):
        """
        Function `delete_all_msg_timestamp` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        deletion_count = tmb.delete_all_msg_timestamp(array)
        self.assertEqual(deletion_count, -1)

    def test_read_most_recent_ship_pos1(self):
        """
        Function `read_most_recent_ship_pos` takes a JSON parsable string as an input.
        Returns: list of ship documents
        """
        tmb = TMB_DAO(True)
        ships = tmb.read_most_recent_ship_pos(self.batch)
        self.assertTrue(type(ships) is list)

    def test_read_most_recent_ship_pos2(self):
        """
        Function `read_most_recent_ship_pos` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        ships = tmb.read_most_recent_ship_pos(array)
        self.assertEqual(ships, -1)

    def test_read_pos_MMSI1(self):
        """
        Function `read_pos_MMSI` takes a JSON parsable string as an input.
        Returns: a position document
        """
        tmb = TMB_DAO(True)
        ships = tmb.read_pos_MMSI(self.batch)
        self.assertTrue(type(ships) is dict)

    def test_read_pos_MMSI2(self):
        """
        Function `read_pos_MMSI` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True)
        array = json.loads(self.batch)
        document = tmb.read_pos_MMSI(array)
        self.assertEqual(document, -1)

    def test_read_vessel_info1(self):
        """
        Function `read_vessel_info` takes a JSON parsable string as an input.
        Returns: a vessel document
        """
        tmb = TMB_DAO(True)
        ships = tmb.read_vessel_info(self.batch)
        self.assertTrue(type(ships) is dict)

    def test_read_vessel_info2(self):
        """
        Function `read_vessel_info` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True)
        array = json.loads(self.batch)
        document = tmb.read_vessel_info(array)
        self.assertEqual(document, -1)

    def test_read_most_recent_ship_pos_in_tile1(self):
        """
        Function `read_most_recent_ship_pos_in_tile` takes a JSON parsable string as an input.
        Returns: list of ship documents
        """
        tmb = TMB_DAO(True)
        ships = tmb.read_most_recent_ship_pos(self.batch)
        self.assertTrue(type(ships) is list)

    def test_read_most_recent_ship_pos_in_tile2(self):
        """
        Function `read_most_recent_ship_pos_in_tile` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        ships = tmb.read_most_recent_ship_pos(array)
        self.assertEqual(ships, -1)     

    def test_read_all_ports1(self):
        """
        Function `read_all_ports` takes a JSON parsable string as an input.
        Returns: list of Port documents
        """
        tmb = TMB_DAO(True)
        ships = tmb.read_most_recent_ship_pos(self.batch)
        self.assertTrue(type(ships) is list)

    def test_read_all_ports2(self):
        """
        Function `read_all_ports` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        ships = tmb.read_most_recent_ship_pos(array)
        self.assertEqual(ships, -1) 

    def test_all_ship_pos_scale3_1(self):
        """
        Function `read_all_ship_pos_scale3` takes a JSON parsable string as an input.
        Returns: list of (Port or Position) documents
        """
        tmb = TMB_DAO(True)
        documents = tmb.read_all_ship_pos_scale3(self.batch)
        self.assertTrue(type(documents) is list)

    def test_all_ship_pos_scale3_2(self):
        """
        Function `read_all_ship_pos_scale3` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        documents = tmb.read_all_ship_pos_scale3(array)
        self.assertEqual(documents, -1)   

    def test_read_last_5_pos1(self):
        """
        Function `read_last_5_pos` takes a JSON parsable string as an input.
        Returns: a list of documents
        """
        tmb = TMB_DAO(True)
        document = tmb.read_last_5_pos(self.batch)
        self.assertTrue(type(document) is list)

    def test_read_last_5_pos2(self):
        """
        Function `read_last_5_pos` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True) 
        array = json.loads(self.batch)
        document = tmb.read_last_5_pos(array)
        self.assertEqual(document, -1)

    def test_read_position_to_port_id1(self):
        """
        Function 'read_position_to_port_id' takes a JSON parsable string as an input.
        Returns: a list of documents
        """
        tmb = TMB_DAO(True)
        document = tmb.read_position_to_port_id(self.batch)
        self.assertTrue(type(document) is list)

    def test_read_position_to_port_id2(self):
        """
        Function `read_position_to_port_id` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True)
        array = json.loads(self.batch)
        document = tmb.read_position_to_port_id(array)
        self.assertEqual(document, -1)

    def test_read_position_given_port1(self):
        """
        Function 'read_position_given_port' takes a JSON parsable string as an input.
        Returns: a list of documents
        """
        tmb = TMB_DAO(True)
        document = tmb.read_position_given_port(self.batch)
        self.assertTrue(type(document) is list)

    def test_read_position_given_port2(self):
        """
        Function `read_position_given_port` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True)
        array = json.loads(self.batch)
        document = tmb.read_position_given_port(array)
        self.assertEqual(document, -1)

    def test_find_tiles_zoom_2_1(self):
        """
        Function 'find_tiles_zoom_2' takes a JSON parsable string as an input.
        Returns: a list of documents
        """
        tmb = TMB_DAO(True)
        document = tmb.find_tiles_zoom_2(self.batch)
        self.assertTrue(type(document) is list)

    def test_find_tiles_zoom_2_2(self):
        """
        Function `find_tiles_zoom_2` fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True)
        array = json.loads(self.batch)
        document = tmb.find_tiles_zoom_2(array)
        self.assertEqual(document, -1)  

    def test_find_tile_from_id1(self):
        """
        Function 'find_tile_from_id' takes a JSON parsable string as an input.
        Returns: a png file (binary data)
        """
        tmb = TMB_DAO(True)
        document = tmb.find_tile_from_id(self.batch)
        self.assertTrue(type(document) is bytes)

    def test_find_tile_from_id2(self):
        """
        Function 'find_tile_from_id' fails nicely if input is not JSON parsable, or is empty.
        """
        tmb = TMB_DAO(True)
        array = json.loads(self.batch)
        document = tmb.find_tile_from_id(array)
        self.assertEqual(document, -1)


if __name__ == '__main__':
    unittest.main()