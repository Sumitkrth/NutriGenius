import pandas as pd

yoga_poses_df = pd.read_csv('dataset\yoga_poses_final.csv')
detailed_procedures_df = pd.read_csv('dataset\yoga_poses_detailed_procedures_full.csv')

# Function to find yoga poses based on user input
def find_yoga_poses(health_issues, user_contraindications):
    all_matches = pd.DataFrame()
    for issue in health_issues:
        matches = yoga_poses_df[yoga_poses_df['Benefit'].str.contains(issue, case=False, na=False)]
        all_matches = pd.concat([all_matches, matches])
    
    # Filter out yoga poses that have contraindications matching any of the user's contraindications
    if not all_matches.empty:
        all_matches = all_matches.drop_duplicates().reset_index(drop=True)
        filtered_matches = []
        for index, row in all_matches.iterrows():
            contraindications_list = row['Contraindications'].split(', ') if isinstance(row['Contraindications'], str) else []
            if not any(contra in user_contraindications for contra in contraindications_list):
                filtered_matches.append(row)
        
        if filtered_matches:
            for row in filtered_matches:
                pose = row['Pose']
                benefit = row['Benefit']
                procedure = detailed_procedures_df[detailed_procedures_df['Pose'] == pose]['Procedure'].values
                procedure_text = procedure[0] if len(procedure) > 0 else "Procedure not available."
                print(f"Pose: {pose}")
                print(f"Benefit: {benefit}")
                print(f"Procedure: {procedure_text}\n")
        else:
            print("No matching yoga poses found for the given health issues.")
    else:
        print("No matching yoga poses found for the given health issues.")

# Main program
if __name__ == "__main__":
    health_issues = []
    user_contraindications = []

    # Asking for health issues
    user_input = input("Please enter your health issue: ").strip()
    health_issues.append(user_input)
    while True:
        more_issues = input("If you have more issues, please enter them. If not, enter 'no': ").strip().lower()
        if more_issues == 'no':
            break
        else:
            health_issues.append(more_issues)

    # Find all poses beneficial for the user's health issues
    all_matches = pd.DataFrame()
    for issue in health_issues:
        matches = yoga_poses_df[yoga_poses_df['Benefit'].str.contains(issue, case=False, na=False)]
        all_matches = pd.concat([all_matches, matches])
    
    # Gather unique contraindications from the matched poses
    contraindications_set = set()
    for index, row in all_matches.iterrows():
        contraindications_list = row['Contraindications'].split(', ') if isinstance(row['Contraindications'], str) else []
        contraindications_set.update(contraindications_list)
    
    # Ask the user about their contraindications
    if contraindications_set:
        print("Please enter any of the following contraindications you have (separate by comma if multiple):")
        print(", ".join(contraindications_set))
        user_contraindications_input = input().title().strip()
        user_contraindications = [contra.strip() for contra in user_contraindications_input.split(',') if contra.strip() in contraindications_set]

    # Find and print the matching yoga poses
    find_yoga_poses(health_issues, user_contraindications)
