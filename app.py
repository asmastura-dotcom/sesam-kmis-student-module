def create_demo_data():
    """Create demo students with realistic names while preserving warning scenarios."""
    data = {
        "student_number": ["S001", "S002", "S003", "S004", "S005", "S006", "S007", "S008", "S009", "S010", "S011", "S012", "S013"],
        "name": [
            "Santos, Maria Concepcion R.",           # S001 – fully compliant
            "Dela Cruz, Jose Mari P.",               # S002 – missing POS
            "Fernandez, Kristoffer Ivan M.",         # S003 – PhD written failed
            "Lopez, Maria Isabella T.",              # S004 – low GWA
            "Villanueva, Gabriel Angelo S.",         # S005 – thesis outline not approved
            "Reyes, Patricia Anne G.",               # S006 – MS exam missing
            "Gomez, Emmanuel D.",                    # S007 – committee deadline near
            "Mendoza, Catherine Joy L.",             # S008 – coursework incomplete
            "Santiago, Rommel C.",                   # S009 – PhD oral failed
            "Ramirez, Maria Lourdes E.",             # S010 – committee changed
            "Torres, Victor Emmanuel A.",            # S011 – coursework changed
            "Bautista, Anna Patricia F.",            # S012 – defended MS
            "Aquino, Francis Joseph T."              # S013 – graduation applied
        ],
        "last_name": ["Santos", "Dela Cruz", "Fernandez", "Lopez", "Villanueva", "Reyes", "Gomez", "Mendoza", "Santiago", "Ramirez", "Torres", "Bautista", "Aquino"],
        "first_name": ["Maria Concepcion", "Jose Mari", "Kristoffer Ivan", "Maria Isabella", "Gabriel Angelo", "Patricia Anne", "Emmanuel", "Catherine Joy", "Rommel", "Maria Lourdes", "Victor Emmanuel", "Anna Patricia", "Francis Joseph"],
        "middle_name": ["R.", "P.", "M.", "T.", "S.", "G.", "D.", "L.", "C.", "E.", "A.", "F.", "T."],
        # Rest of the columns remain exactly as before (program, gwa, units, etc.)
        # ... (keep all other columns identical to the previous create_demo_data)
