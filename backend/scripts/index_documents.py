import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.db.session import SessionLocal
from app.services.rag.indexer import document_indexer
import logging


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main execution script to scan the local medical library and 
    populate the pgvector database chunks.
    """
    
    
    db = SessionLocal()
    
    try:
        print("\n" + "🚀" + " Starting Medical Document Indexing...".center(58))
        print("=" * 60)
        

        docs_path = BASE_DIR / "data" / "raw" / "medical_pdfs"
        
       
        if not docs_path.exists():
            print(f"❌ Directory not found: {docs_path}")
            print("\nAction required: Please create the directory and add files:")
            print(f"   mkdir -p {docs_path}")
            print(f"   # Then add PDF/DOCX/TXT medical records to that folder.")
            return
        
      
        all_files = list(docs_path.rglob("*"))
        doc_files = [
            f for f in all_files 
            if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt']
        ]
        
        if not doc_files:
            print(f"❌ No valid documents found in: {docs_path}")
            print("Supported formats: PDF, DOCX, TXT")
            return
        
        print(f"📁 Source: {docs_path}")
        print(f"📄 Found {len(doc_files)} documents to index")
        print("-" * 60)
        
       
        stats = document_indexer.index_directory(
            directory_path=str(docs_path), 
            db=db,
            custom_metadata={"indexing_session": "manual_bulk_import_2026"}
        )
        
      
        print("\n" + "=" * 60)
        print("✅ INDEXING COMPLETE!".center(60))
        print("=" * 60)
        print(f"   Files indexed:   {stats['total_files']}")
        print(f"   Chunks created: {stats['total_chunks']}")
        
       
        if stats.get('failed'):
            print(f"\n❌ Failed files: {len(stats['failed'])}")
            for fail in stats['failed']:
                print(f"   - {Path(fail['file']).name}: {fail['error']}")
        
        print("-" * 60)
        print("\n🎉 Your Rural AI Medical Knowledge Base is now LIVE!")
        print("   The local database is populated with searchable vector embeddings.")
        print("   You can now start the API and use the /rag/query endpoint.\n")
        
    except Exception as e:
        print(f"\n❌ Critical System Error: {e}")
        logger.exception("Indexing aborted due to error.")
    
    finally:
       
        db.close()

if __name__ == "__main__":
    main()