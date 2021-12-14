# AIS Project: Monitoring Ships at Sea Milestone 4
by Brian Walker, Monika Krcoski, Hailey Leonard

## To install the database to your device: 
- Download the `AISTestData_dump.mysql` included in this project directory.  
- Open a terminal, and set your directory to the folder which contains `AISTestData_dump.mysql`.  
- Run `$ mysql -u <user> -p < AISTestData_dump.mysql` in the system shell with your username in place of `<user>`.

## To run the DAO:
- Open a terminal and set the directory to the folder which contains this project.
- Run `tmb_dao.py` using Python.

## Project State of Completion:
This project implements all priority 1, 2, and 3 queries,  
along with all priority 4 queries except finding the 4 tiles of zoom level 2.

Unit tests are written for each function to verify return type and ability to run on the interface.  
Integration tests are not implemented.

## The Data Schema:
### Data is split into the following tables with these values:
AIS_MESSAGE(Id, Timestamp, MMSI, Class, Vessel_IMO)
VESSEL(IMO, Flag, Name, Built, CallSign, Length, Breadth, Tonnage, MMSI, Type, Status, Owner)  
MAP_VIEW(Id, Name, LongitudeW, LatitudeS, LongitudeE, LatitudeN, Scale, RasterFile, ImageWidth, ImageHeight, ActualLongitudeW, ActualLatitudeS, ActualLongitudeE, ActualLatitudeN, ContainerMapView_Id)
PORT(Id, LoCode, Name, Country, Longitude, Latitude, Website, MapView1_Id, MapView2_Id, MapView3_Id)  
STATIC_DATA(AISMessage_Id, AIS_IMO, CallSign, Name, VesselType, CargoType, Length, Breadth, Draught, AISDestination, ETA, DestinationPort_Id)
POSITION_REPORT(AISMessage_Id, NavigationalStatus, Longitude, Latitude, RoT, SoG, CoG, Heading, LastStaticData_Id, MapView1_Id, MapView2_Id, MapView3_Id)  
USER(EmailAddress, Name, PasswordHash, ApplicationSetting1, ApplicationSetting2, ApplicationSetting3)  
MONITOR_VESSEL(User_EmailAddress, Vessel_IMO, DateStarted, DateEnded)  
MONITOR_PORT(User_EmailAddress, Port_Id, DateStarted, DateEnded)
