import os
import sys
from neo4j import GraphDatabase

# Using os.environ[] instead of os.getenv() enforces that the key MUST exist.
# If the variable is missing, Python will immediately throw a KeyError.
try:
    NEO4J_URI = os.environ["NEO4J_URI"]
    NEO4J_USER = os.environ["NEO4J_USER"]
    NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
except KeyError as e:
    print(f"Configuration Error: Missing required environment variable {e}", file=sys.stderr)
    print("Please ensure your local .env file is configured correctly.", file=sys.stderr)
    sys.exit(1)

CONSTRAINTS = [
    "CREATE CONSTRAINT manufacturer_id IF NOT EXISTS FOR (m:Manufacturer) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:MedicalDevice) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT sku_id IF NOT EXISTS FOR (s:SKU) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT unspsc_code IF NOT EXISTS FOR (c:UNSPSC_Category) REQUIRE c.code IS UNIQUE"
]

def initialize_database():
    print(f"Connecting to Neo4j instance at: {NEO4J_URI}")

    
    try:
        # If the driver fails to connect here, it throws and exception
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            print("Applying structural ontology constraints...")
            for constraint in CONSTRAINTS:
                session.run(constraint)
            print("Ontology schema initialized successfully!")
            
            result = session.run("SHOW CONSTRAINTS")
            print("\nActive System Constraints:")
            for record in result:
                print(f" - [{record['type']}] {record['name']} on property {record['properties']}")

        driver.close()        

    except Exception as e:
        print(f"Schema initialization failed: {e}", file=sys.stderr)
        sys.exit(1)        

if __name__ == "__main__":
    initialize_database()