import requests
import json
import time

# Ensure your app.py is running on this port
API_URL = "http://localhost:5005/evaluate"

# 10 Sample Students with different profiles
students = [
    {"name": "Alice Johnson", "student_id": "STU_001", "group": "Biology", "ambition": "Doctor"},
    {"name": "Bob Smith", "student_id": "STU_002", "group": "Computer Science", "ambition": "Software Engineer"},
    {"name": "Charlie Brown", "student_id": "STU_003", "group": "Commerce", "ambition": "Chartered Accountant"},
    {"name": "Diana Prince", "student_id": "STU_004", "group": "Arts", "ambition": "Graphic Designer"},
    {"name": "Ethan Hunt", "student_id": "STU_005", "group": "Mathematics", "ambition": "Data Scientist"},
    {"name": "Fiona Gallagher", "student_id": "STU_006", "group": "Bio-Maths", "ambition": "Biotechnologist"},
    {"name": "George Miller", "student_id": "STU_007", "group": "Economics", "ambition": "Financial Analyst"},
    {"name": "Hannah Abbott", "student_id": "STU_008", "group": "Humanities", "ambition": "Psychologist"},
    {"name": "Ian Wright", "student_id": "STU_009", "group": "Engineering", "ambition": "Mechanical Engineer"},
    {"name": "Jenny Kim", "student_id": "STU_010", "group": "Design", "ambition": "Fashion Architect"}
]

def run_batch_test():
    print(f"🚀 Starting batch test for {len(students)} students...\n")
    
    for i, student in enumerate(students, 1):
        print(f"[{i}/10] Sending request for {student['name']} ({student['student_id']})...")
        
        # Adding some basic fields to satisfy the API formatter
        data = {
            "student_id": student["student_id"],
            "name": student["name"],
            "school": "Testing Academy",
            "group": student["group"],
            "year": "2025-26",
            "ambition_specify": student["ambition"],
            "subjects_liked": [student["group"], "General Excellence"],
            "cognitive": {
                "maths_comfort": "Moderate",
                "problem_solving": "Systematic"
            },
            "life_skills": {
                "q1_confident": "Yes"
            }
        }
        
        try:
            response = requests.post(API_URL, json=data)
            if response.status_code == 200:
                result = response.json()
                usage = result.get("token_usage", {})
                cost_inr = usage.get("cost_inr", 0)
                print(f"   ✅ Success! Tokens: {usage.get('total_tokens')} (Cost: ₹{cost_inr})")
            else:
                print(f"   ❌ Failed with status code: {response.status_code}")
                print(f"      Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error connecting to API: {e}")
        
        # Small delay to allow file writing to settle
        time.sleep(1)

    print("\n✨ Batch test complete! Open 'token_usage.xlsx' to view the 10 records.")

if __name__ == "__main__":
    run_batch_test()
