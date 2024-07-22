def init_db(CONNECTION_POOL):
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        # File Metadata Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                course TEXT NOT NULL,
                profs TEXT NOT NULL,
                year INTEGER NOT NULL,
                semester TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_ID TEXT NOT NULL,
                file_link TEXT NOT NULL,
                uploaded_by TEXT NOT NULL
            )
        ''')
        # Course Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # Professors Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # File Types Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_types (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # Years Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS years (
                id SERIAL PRIMARY KEY,
                name INTEGER NOT NULL  -- Changed from TEXT to INTEGER
            )
        ''')
        # Semesters Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semesters (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # Suggestions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id SERIAL PRIMARY KEY,
                suggestion TEXT NOT NULL
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM professors')
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Names/names SBA.txt', 'Names/names CEN.txt', 'Names/names CAS.txt', 'Names/names CAAD.txt']
            done_name = []
            for i in files:
                with open(i, 'r') as file:
                    names = file.readlines()
                    for name in names:
                        name = name.strip()                    
                        if name:  
                            if name not in done_name: 
                                done_name.append(name)
                                cursor.execute('INSERT INTO professors (name) VALUES (%s)', (name,))

        cursor.execute('SELECT COUNT(*) FROM courses')
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Names/Courses.txt']
            done_name = []
            for i in files:
                with open(i, 'r') as file:
                    names = file.readlines()
                    for name in names:
                        name = name.strip()                    
                        if name:  
                            if name not in done_name: 
                                done_name.append(name)
                                cursor.execute('INSERT INTO courses (name) VALUES (%s)', (name,))
        
        cursor.execute('SELECT COUNT(*) FROM semesters') 
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Fall', 'Spring', 'Summer', 'Unkown']
            for name in files:
                cursor.execute('INSERT INTO semesters (name) VALUES (%s)', (name,))
        
        cursor.execute('SELECT COUNT(*) FROM file_types')
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Midterm 1', 'Midterm 2', 'Midterm 3', 'Final', 'Quiz', 'Assignment', 'Notes', 'Syllabus', 'Book', 'Book Answer Key','Others']
            for name in files:
                cursor.execute('INSERT INTO file_types (name) VALUES (%s)', (name,))