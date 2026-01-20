import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import get_db

db = get_db()
photos = db.execute('SELECT COUNT(*) as count FROM photos')
faces = db.execute('SELECT COUNT(*) as count FROM faces')
faces_per_photo = db.execute('''
    SELECT 
        COUNT(DISTINCT photo_id) as photos_with_multiple_faces
    FROM faces
    GROUP BY photo_id
    HAVING COUNT(*) > 1
''')

multi_face_count = len(faces_per_photo) if faces_per_photo else 0

print("=" * 60)
print("DATABASE STATS AFTER REPROCESSING")
print("=" * 60)
print(f"Total photos: {photos[0]['count']}")
print(f"Total faces: {faces[0]['count']}")
print(f"Average faces per photo: {faces[0]['count'] / photos[0]['count']:.2f}")
print(f"Photos with multiple faces: {multi_face_count}")
print("=" * 60)
