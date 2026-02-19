import weaviate

from config import WEAVIATE_LOCAL_PORT, WEAVIATE_GRPC_PORT


def reset_schema():
    # Connect to Weaviate
    client = weaviate.connect_to_local(port=WEAVIATE_LOCAL_PORT, grpc_port=WEAVIATE_GRPC_PORT)
    
    collection_name = "BookChunk1"
    
    try:
        # Check if it exists
        if client.collections.exists(collection_name):
            # Delete it
            client.collections.delete(collection_name)
            print(f"✅ Collection '{collection_name}' has been successfully deleted.")
        else:
            print(f"⚠️  Collection '{collection_name}' was not found (maybe already deleted?).")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    reset_schema()
