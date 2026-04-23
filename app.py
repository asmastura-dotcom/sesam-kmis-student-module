<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SESAM Student Module – Name Format: Last, First Middle</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 700px; margin: auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h2, h3 { color: #2c7da0; }
        label { font-weight: bold; display: block; margin-top: 12px; }
        input, select, button { width: 100%; padding: 8px; margin-top: 5px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        .name-row { display: flex; gap: 10px; }
        .name-row div { flex: 1; }
        button { background-color: #2c7da0; color: white; border: none; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #1f5e7a; }
        .student-card { background: #f9f9f9; border-left: 4px solid #2c7da0; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .student-name { font-size: 1.1em; font-weight: bold; color: #1f5e7a; }
        hr { margin: 20px 0; }
    </style>
</head>
<body>
<div class="container">
    <h2>SESAM Student Module – Program Selection</h2>
    <form id="studentForm">
        <div class="name-row">
            <div>
                <label>Last Name</label>
                <input type="text" id="lastName" placeholder="Dela Cruz" required>
            </div>
            <div>
                <label>First Name</label>
                <input type="text" id="firstName" placeholder="Juan" required>
            </div>
            <div>
                <label>Middle Name</label>
                <input type="text" id="middleName" placeholder="Santos (optional)">
            </div>
        </div>

        <label>Student Number</label>
        <input type="text" id="studentNumber" placeholder="2025-00123" required>

        <label>Select Program</label>
        <select id="programSelect" required>
            <option value="">-- Choose a program --</option>
            <option value="MS Environmental Science">MS Environmental Science</option>
            <option value="PhD Environmental Science">PhD Environmental Science</option>
            <option value="PhD Environmental Diplomacy and Negotiations">PhD Environmental Diplomacy and Negotiations</option>
            <option value="Master in Resilience Studies (M-ReS)">Master in Resilience Studies (M-ReS)</option>
            <option value="Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)">Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)</option>
        </select>

        <label>Year Admitted</label>
        <input type="number" id="yearAdmitted" value="2026" required>

        <button type="submit">Register Student</button>
    </form>

    <hr>
    <h3>Registered Students (Lastname, Firstname Middlename)</h3>
    <div id="studentList" class="student-list"></div>
</div>

<script>
    // Load existing students from browser's local storage
    let students = JSON.parse(localStorage.getItem('sesamStudents')) || [];

    // Helper: format name as "Lastname, Firstname Middlename"
    function formatName(last, first, middle) {
        let full = `${last}, ${first}`;
        if (middle && middle.trim() !== "") {
            full += ` ${middle.trim()}`;
        }
        return full;
    }

    // Program-specific thesis units (from ISSP document)
    function getMilestones(program) {
        if (program.includes('MS')) return 'Thesis units: 6 | Comprehensive exam: required';
        if (program.includes('PhD Environmental Science')) return 'Thesis units: 12 | Comprehensive exam: required';
        if (program.includes('PhD Environmental Diplomacy')) return 'Thesis units: 12 | Diplomacy practicum required';
        if (program.includes('Resilience')) return 'Capstone project required';
        if (program.includes('Tropical Marine')) return 'Professional thesis / case study';
        return 'Consult advisor for milestone details';
    }

    function displayStudents() {
        const container = document.getElementById('studentList');
        if (!container) return;
        if (students.length === 0) {
            container.innerHTML = '<p>No students registered yet.</p>';
            return;
        }
        container.innerHTML = students.map((s, idx) => `
            <div class="student-card">
                <div class="student-name">${formatName(s.lastName, s.firstName, s.middleName)}</div>
                <div>Student #: ${s.studentNumber}</div>
                <div>Program: ${s.program}</div>
                <div>Admitted: ${s.year}</div>
                <div><small>${getMilestones(s.program)}</small></div>
            </div>
        `).join('');
    }

    // Handle form submission
    document.getElementById('studentForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const lastName = document.getElementById('lastName').value.trim();
        const firstName = document.getElementById('firstName').value.trim();
        const middleName = document.getElementById('middleName').value.trim();
        const studentNumber = document.getElementById('studentNumber').value.trim();
        const program = document.getElementById('programSelect').value;
        const year = document.getElementById('yearAdmitted').value;

        if (!lastName || !firstName || !studentNumber || !program) {
            alert('Please fill all required fields (Last Name, First Name, Student Number, Program).');
            return;
        }

        const newStudent = {
            id: Date.now(),
            lastName: lastName,
            firstName: firstName,
            middleName: middleName,
            studentNumber: studentNumber,
            program: program,
            year: year,
            registeredOn: new Date().toISOString()
        };
        students.push(newStudent);
        localStorage.setItem('sesamStudents', JSON.stringify(students));
        displayStudents();
        document.getElementById('studentForm').reset();
    });

    // Show existing students on page load
    displayStudents();
</script>
</body>
</html>
