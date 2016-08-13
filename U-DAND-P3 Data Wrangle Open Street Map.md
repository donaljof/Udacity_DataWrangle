
# Data Wrangle Open Street Map
### Udacity DAND Project - Donal O Farrell

#### Map Area
Area chosen for this project was the metro extract of Dublin, Ireland. Choosen as this is the city in which I currently reside and the capitol of the country I was born (also the only decent sized city in it).

https://mapzen.com/data/metro-extracts/odes/extracts/aa4d980d61fa

Uncompressed osm file size = 258 MB  
nodes.csv = 89 MB  
nodes_tags.csv = 4 MB  
ways.csv 11 MB  
way_nodes.csv = 36 MB  
ways_tags.csv = 23 MB  
osm_dublin.db = 215 MB  


#### Data Problems Encountered

* ##### Irregular street abbreviations.
Upon parsing and importing data set for first time, irregular street naming used such Rd. for Road found in dataset. Street naming converter function using regular expressions employed as part of shape_element function of OSM file parser and CSV generation.

* ##### Inconsistant use of addr:city tag.
Analysis of output of addr:city tag shows inconsistant values. Some nodes/ways are tagged based on the area of Dublin in which they are located, such as "Cabinteely", some use the [Dublin City Postal codes](https://en.wikipedia.org/wiki/List_of_Dublin_postal_districts) and some reference Dublin only. Unless the area in question is outside of the city of Dublin and a town/village in its own right this tag value has been updated to the correct city code or to simply "Dublin". 


```python
########Street name fixer#########
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

#Creating regular expressions to locate abreviations to street naming.
avenue_re = re.compile(r'\bave?\.?\b', re.IGNORECASE)
street_re = re.compile(r'\stre?\.?\b', re.IGNORECASE)
road_re = re.compile(r'\rd\.?\b', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

# Updated to have regular expressions for finding street name mappings
mapping = { street_re: "Street",
            avenue_re: "Avenue",
            road_re: "Road"
            }
            
def street_converter(name, mapping):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        #Look for street names not in regular convention and update based on re mapping
        if street_type not in expected:
            for reg_exp in mapping:
                if reg_exp.search(name[name.find(street_type):]):
                    name = name[:name.find(street_type)] + mapping[reg_exp]               
    return name
```


```python
############ Update functions to handle data cleaning:  
      
dublin_re = re.compile(r'Dublin ?[0-9]?[0-9W]?$')
#Towns/villages seperate from Dublin, some are within the county of Dublin so this
#is somewhat subjective classififcation. It should be noted some of these towns are
#not in the county of Dublin at all.
not_dublin = ['Celbridge','Lucan','Leixlip','Malahide','Bray','Portmarnock',\
    'Kilternan','Dunshaughlin','Donabate','Batterstown','Baldonnel']
#Areas of Dublin are assigned, though not consistantly, using the Dublin area
#code. Again assignment of areas on the outskirts of the city but within 
#the county is subjective.
in_dublin = {'Dublin':['Killiney','Blackrock','Harristown','Swords','Stillorgan',\
    'Dún Laoghaire','Monkstown','Mount Merrion','Cornelscourt'],\
    'Dublin 15':['Ongar','Blanchardstown'], 'Dublin 18': ['Cabinteely'],\
    'Dublin 14': ['Rathfarnham','Churchtown'], 'Dublin 4':['Donnybrook'],\
    'Dublin 24':['Tallaght'],'Dublin 22': ['Clondalkin'],'Dublin 3': ['Clontarf'] }

def city_converter(value):
    #value = str(value_unicode)  -fails when converting ú in Dún Laoghaire
    match = False
    if re.search(dublin_re,value):
        match = True
        return value
    elif value in not_dublin:
        match = True
        return value
    else:
        for d in in_dublin:
            for address in in_dublin[d]:
                if value == unicode(address, 'utf-8'): 
                #Many unicode related frustrations before unicode converter was added due to non-equality of unicode and stings.
                    match = True
                    return d           
    if match == False:        
        return 'Dublin'
```

#### SQL Database Generation

Using the csv file output from OSM_CSV_GENERATOR.py a SQLite database was created using the following schema:
```SQL
PRAGMA encoding = "UTF-8"; 

CREATE TABLE nodes(
n\ "id" TEXT PRIMARY KEY,
"lat" FLOAT,
"lon" FLOAT,
"user" TEXT,
"uid" TEXT,
"version" TEXT,
"changeset" TEXT,
"timestamp" TEXT
);
CREATE TABLE node_tags(
"node id" TEXT,
"key" TEXT,
"value" TEXT,
"type" TEXT,
FOREIGN KEY("node id") REFERENCES nodes("id")
);
CREATE TABLE ways(
"id" TEXT PRIMARY KEY,
"user" TEXT,
"uid" TEXT,
"version" TEXT,
"changeset" TEXT,
"timestamp" TEXT
);
CREATE TABLE way_tags(
"way_id" TEXT,
"key" TEXT,
"value" TEXT,
"type" TEXT,
FOREIGN KEY ("way_id") REFERENCES ways("id")
);
CREATE TABLE way_nodes(
"way_id" TEXT,
"node_id" TEXT,
"position" TEXT,
FOREIGN KEY("way_id") REFERENCES ways("id"),
FOREIGN KEY("node_id") REFERENCES nodes("id")
);
CREATE TABLE users(
"uid" TEXT PRIMARY KEY,
"user" TEXT,
"changes" INTERGER
);
```
Where users table DATA was generated using:
```SQL
INSERT INTO users
SELECT user, uid, COUNT(*) as changes
FROM (SELECT user, uid FROM nodes UNION ALL SELECT user, uid FROM ways)
GROUP BY uid;
```




#### Database Queries and Questions

##### Total Number of nodes and ways?

```SQL
SELECT COUNT(*) FROM nodes;
```
1109902

```SQL
SELECT COUNT(*) FROM ways;
```
194691

##### What are the top contributors to this map?

```SQL
SELECT uid, user,changes, ((changes * 100.00) / (SELECT SUM(changes) FROM users)) AS Percentage_Changes 
FROM users 
ORDER BY changes DESC 
LIMIT 10;
```
|User|UID|Changes|Percent Of Total|
|:--|:--|:--|:--|:--|
|Nick Burrett|166593|233375|17.8887208501042|
|mackerski|6367|186843|14.3219379530628|
|Dafo43|114051|155012|11.8820199096576|
|brianh|19612|154798|11.8656163263179|
|VictorIE|2008037|73067|5.60075057891618|
|Conormap|2354|63804|4.89072070753101|
|Ignobilis|6180|51730|3.96522133722931|
|Autarch|4553|22617|1.73364413269119|
|wigs|124925|20494|1.57091138768949|
|Blazejos|15535|19143|1.46735418632478|

##### What are the most common node tag keys?

```SQL
SELECT key, COUNT(*) AS num 
FROM node_tags 
GROUP BY key 
ORDER BY num DESC LIMIT 10;
```
|Key|Num|
|:--|:--|
|created_by|11299|
|highway|11081|
|name|10507|
|street|8143|
|amenity|6186|
|city|6010|
|housenumber|5959|
|natural|5763|
|operator|3846|
|barrier|3711|

##### What are the most common amenity values?

```SQL
SELECT value, COUNT(*) AS num 
FROM node_tags WHERE key = "amenity" 
GROUP BY value 
ORDER BY num DESC LIMIT 10;
```
|Amenity|Num|
|:--|:--|
|restaurant|528|
|fast_food|520|
|cafe|496|
|post_box|469|
|pub|464|
|bench|455|
|bicycle_parking|315|
|pharmacy|253|
|parking|230|
|atm|209|

##### Are there any pubs in Dublin with the same name? 
```SQL
SELECT pub_name, num
FROM (
SELECT pub_name, COUNT(pub_name) as num
FROM (
SELECT n0.id AS id, n1.value AS pub_name, n1.key AS k1
FROM nodes n0, node_tags n1, 
(SELECT "node id" AS id 
FROM node_tags
WHERE node_tags.key = "amenity" AND node_tags.value = "pub") n2
WHERE n0.id = n2.id AND n1."node id" = n0.id)
WHERE k1 = "name"
GROUP BY pub_name)
WHERE num > 1
ORDER BY num DESC;
```
|Pub Name|Num|
|:--|:--|
|Sweeney's|3|
|The Village Inn|3|
|Brady's|2|
|Downey's|2|
|Hill 16|2|
|Madigan's|2|
|O'Donoghue's|2|
|Ryan's|2|
|The Laurels|2|
|The Lombard|2|
|The Waterside|2|
|The Willows|2|

##### What are the most common way tag keys?
```SQL
SELECT key, COUNT(*) AS num 
FROM way_tags 
GROUP BY key 
ORDER BY num DESC LIMIT 10;
```
|Key|Num|
|:--|:--|
|building|101789|
|street|76337|
|housenumber|66420|
|highway|59314|
|levels|50122|
|house|43109|
|name|34676|
|roof:shape|29595|
|maxspeed|25484|
|ga|12007|

##### What are the most common highway way tags? 
```SQL
SELECT value, COUNT(*) AS num 
FROM way_tags 
WHERE key = "highway" 
GROUP BY value 
ORDER BY num DESC LIMIT 10;
```
|Highway|Num|
|:--|:--|
|residential|18201|
|service|16154|
|footway|9659|
|secondary|3891|
|unclassified|2825|
|tertiary|2626|
|path|1589|
|track|1293|
|steps|724|
|pedestrian|506|

##### How many ways contain cycle paths and how many ways are dedicated cyclepaths?

```SQL
SELECT COUNT(*)
FROM way_tags w0,(SELECT * FROM way_tags
WHERE key = "highway" AND value IN ("residential", "service", "footway", "secondary", "unclassified", "tertiary")) w1
WHERE w0.way_id = w1.way_id AND w0.key = "cycleway";
```
986

```SQL
SELECT COUNT(*) 
FROM way_tags, ways
WHERE way_tags.key = "highway" AND way_tags.way_id = ways.id AND way_tags.value = "cycleway" ;
```
390

```SQL
SELECT COUNT(*)
FROM way_tags
WHERE key = "highway" AND value IN ("residential", "service", "footway", "secondary", "unclassified", "tertiary");
```
53356

From this a rough number for the amount of cycle friendly roads/streets/paths in Dublin can be calculated: 1376/53356 or 2.58 % of total ways.


## Further Ideas and Discussion

##### Crossing Dublin without passing a pub.

A further extesnsion of the analysis into the pubs of Dublin would be to answer a classic riddle, put forward by James Joyce in the novel Ulysses - "Good puzzle would be cross Dublin without passing a pub."

Using the sqlite database generated above a possible solution would be to use the 'addr:street' tag for nodes tagged as pubs and build a table of streets containing pubs that cannot be used to travel on.
This approach fails pretty quickly as the are a multiude of pub nodes that are not tagged with a street address or not tagged correctly, as an example see two of my local establishments below both on Manor St., Stonybatter.

```XML
<node id="738165500" lat="53.3510474" lon="-6.2823722" version="5" timestamp="2015-12-02T13:04:32Z" changeset="35705672" uid="1909867" user="madmap77">
    <tag k="addr:housenumber" v="19"/>
    <tag k="addr:street" v="Stoneybatter"/>
    <tag k="amenity" v="pub"/>
    <tag k="name" v="Tommy O'Gara"/>
  </node>
  <node id="738165501" lat="53.3508058" lon="-6.2820166" version="4" timestamp="2014-06-30T15:09:57Z" changeset="23351241" uid="64381" user="Tincho">
    <tag k="amenity" v="pub"/>
    <tag k="name" v="The Glimmer Man"/>
    <tag k="website" v="http://www.theglimmer.com/"/>
```

One solution would be to update the node tags for each pub with the street address during the osm xml parsing and csv generation though the deciding the correct street address would be difficult to complete programmaticaly. One possiblity would be to use the 'lat' and 'lon' node attributes to find the nearest way with a 'highway' tag.

Alternatively, instead of finding the nearest way, the 'lat' / 'lon' values could be used to create an exclusion zone around a pub where the potential route cannot pass. This approach has some limitations due to the narrowness of Dublins medieval street layout and may result in streets being blocked that don't acually have pubs on them or the street (there is a pub in a laneway).
Some googling of this problem found this to be the approach taken by Python developer Rory O Connor in solving this pretty comprehensively. (http://www.kindle-maps.com/blog/how-to-walk-across-dublin-without-passing-a-pub-full-publess-route-here.html)

##### A measure of a city's cycle friendliness.

The percentage cycle-able ways caluclated above is a crude first attempt at measuring the amount of cycle friendly routes in the city. As a measure of cycle routes it is deficient in several ways: 
* It does not account for the lenght of the way in real terms.
* Not all cycle friendly roads have 'cycleway' tags associated (observed from personal experience and a review of cycle routes in my local area on OSM).
* Not all road with designated cycle paths are actually cycle friendly (this may be unique to Dublin!)
* The metro area captured in the database used is much larger than central Dublin and includes large sections of the adjacent counties that would ot be considered either Dublin or urban areas.

A refinment of this number would be useful to creating a metric by which to compare the cycle friendliness of different cities around the world. The first step would be to update the percentage cyclable ways to a percentage cyclable distances using the actual lenght of the ways tagged as having cycle paths.

##### Updating streets and addresses with Irish counterparts.

One deficiency in the Dublin OSM map data is the number of nodes and ways that lack a tag for the Irish language (Gaelge) name. This can be seen in the low value for the "ga" key on the tag key summary (12007) compared with the total number of "name" key's (34676). For node_tags key = "ga" did not even make the top ten tags keys but this would be expected as many nodes would have no Irish language equivalent, this is not the case for streets where every street in the Republic of Ireland has an offical translation.

A solution to this problem would be to encourage the top contributors to the Dublin OSM map to include Irish language versions of streets and addresses where possible in the way/node tags and update the map manually with known translations. All streets in Dublin display the irish language version in italics above the english. This of course might work for future map updates but updating the existing data would occur very slowly.

Fortunately a register of all placenames in Ireland and their translation to irish is organized and curated by the Department of Arts, Heritage and the Gealtacht (http://www.logainm.ie/en/). The website even includes a built in browser translator that can translate any list of street or placenames to its Irish equivalent. If the information in the database used for this website could be intergrated programatically into the OSM tag data, this would provide an updated Irish language translation for almost all ways and significant amount of address nodes.

The advantages of this would be a more complete data set for Dublin that includes street and placename data in one of the official languages of ireland. This could be used to create an irish language version of OSM for Dublin and by extension all of ireland. There is also often more historical information contained in the irish language versions of placenames and streetnames in ireland, having this information available in a database could be of value to historians.

A major challenge to this addition would be interacting and using the data on the loganim website. There is no clear way do download the information used to create the placename translator though it must work off a database of some kind. The first step would be to request a usable form of this database for combination with the existing node_tag data, directly emailing the creators of the website should yield results given this is public initiative to promote the irish language. Otherwise a freedom of information request could be submitted. There is also no guarantee that the format of the data recieved will be easy to use (like .csv) and parsing/data cleaning may be needed.
Interacting directly with the translate function of the website is another option but that would be more technically challenging. This would also be potentially much slower than downloading a complete database locally as a new request would be needed for each update and internet connection time would be added to the time each addition.



```python

```
