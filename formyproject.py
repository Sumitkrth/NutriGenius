import pandas as pd
from termcolor import colored

# Function to calculate BMR
def calculate_bmr(weight, height, age, gender):
    if gender == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == 'female':
        return 10 * weight + 6.25 * height - 5 * age - 161
    else:
        print('Invalid gender')
        return None

# Function to calculate daily calorie requirement based on BMR and activity level
def calculate_calories(bmr, activity_level):
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly active': 1.375,
        'moderately active': 1.55,
        'very active': 1.725,
        'extra active': 1.9
    }
    return bmr * activity_multipliers.get(activity_level, 0) if activity_level in activity_multipliers else None

# Function to get user's activity level
def get_activity_level():
    print('Select your activity level:')
    print('1. Sedentary (little or no exercise)')
    print('2. Lightly active (light exercise/sports 1-3 days/week)')
    print('3. Moderately active (moderate exercise/sports 3-5 days/week)')
    print('4. Very active (hard exercise/sports 6-7 days/week)')
    print('5. Extra active (very hard exercise/sports or physical job)')
    
    levels = {
        1: 'sedentary',
        2: 'lightly active',
        3: 'moderately active',
        4: 'very active',
        5: 'extra active'
    }
    try:
        level = int(input('Enter the number corresponding to your activity level: '))
        return levels.get(level, None)
    except ValueError:
        print('Invalid input. Please enter a number between 1 and 5.')
        return None

# Function to get user's diseases
def get_diseases():
    try:
        num_diseases = int(input("How many diseases are you suffering from? "))
        if num_diseases == 0:
            return []
        diseases = [input(f"Enter the name of disease #{i+1}: ").title() for i in range(num_diseases)]
        return diseases
    except ValueError:
        print("Invalid input for number of diseases. Please enter a valid number.")
        return None

# Function to print nutritional component values along with their names
def print_nutritional_components(components):
    nutritional_names = [
        'Carbohydrates', 'Total Fat', 'Saturated Fat', 'Protein', 'Fiber', 
        'Cholesterol', 'Sodium', 'Sugar', 'Potassium', 'Magnesium', 
        'Phosphorus', 'Vitamin C', 'Vitamin A', 'Calcium', 'Iron', 
        'Zinc', 'Vitamin E', 'Vitamin K'
    ]
    for name, value in zip(nutritional_names, components):
        print(f"{name}: {value}")

# Function to calculate default nutritional requirements based on daily calorie needs
def calculate_default_nutritional_requirements(calories):
    # These values are general guidelines based on average recommendations
    carbs = calories * 0.55 / 4  # 55% of calories from carbs, 4 calories per gram of carbs
    fat = calories * 0.25 / 9    # 25% of calories from fat, 9 calories per gram of fat
    protein = calories * 0.20 / 4 # 20% of calories from protein, 4 calories per gram of protein
    fiber = 25  # grams per day, average recommended intake
    cholesterol = 300  # mg per day, maximum recommended intake
    sodium = 2300  # mg per day, maximum recommended intake
    sugar = 50  # grams per day, recommended upper limit
    potassium = 4700  # mg per day, recommended intake
    magnesium = 400  # mg per day, recommended intake
    phosphorus = 700  # mg per day, recommended intake
    vitamin_c = 90  # mg per day, recommended intake
    vitamin_a = 900  # µg per day, recommended intake
    calcium = 1000  # mg per day, recommended intake
    iron = 8  # mg per day, recommended intake
    zinc = 11  # mg per day, recommended intake
    vitamin_e = 15  # mg per day, recommended intake
    vitamin_k = 120  # µg per day, recommended intake

    return [
        carbs, fat, 0, protein, fiber, 
        cholesterol, sodium, sugar, potassium, magnesium, 
        phosphorus, vitamin_c, vitamin_a, calcium, iron, 
        zinc, vitamin_e, vitamin_k
    ]

# Main function to execute the entire script
def main():
    try:
        weight = float(input('Enter your weight in kilograms: '))
        height = float(input('Enter your height in centimeters: '))
        age = int(input('Enter your age: '))
        gender = input('Enter your gender (male/female): ').lower()
    except ValueError:
        print('Invalid input. Please enter numeric values for weight, height, and age.')
        return

    bmr = calculate_bmr(weight, height, age, gender)
    if bmr is not None:
        print(f'Your basal metabolic rate is: {bmr:.2f} calories')

    activity_level = get_activity_level()
    if activity_level is None:
        print('Invalid activity level')
        return

    calories = calculate_calories(bmr, activity_level)
    if calories is not None:
        print(f'Your daily calorie requirement is: {calories:.2f} calories')
    else:
        print('Unable to calculate daily calorie requirement. Check activity level input.')
        return

    diseases = get_diseases()
    if diseases is None:
        print('Invalid diseases input')
        return

    if len(diseases) == 0:
        default_nutrients = calculate_default_nutritional_requirements(calories)
        print("Nutritional component values based on daily calorie requirement:")
        print_nutritional_components(default_nutrients)
        return

    try:
        df1 = pd.read_csv('dataset/final_diseases.csv')
        df2 = pd.read_csv('dataset/final_food_items.csv')
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
        return
    except pd.errors.EmptyDataError:
        print("One of the input files is empty.")
        return

    nutritional_components = []
    for disease in diseases:
        row = df1.loc[df1['Disease'] == disease]
        if row.empty:
            print(f"No data found for disease: {disease}")
            continue
        nutritional_components.append(list(row.iloc[:, 1:].values[0]))

    if not nutritional_components:
        print("No nutritional components found for the given diseases.")
        return

    final_list = nutritional_components[0]
    for components in nutritional_components[1:]:
        for i, value in enumerate(components):
            final_list[i] = min(final_list[i], value)

    print("Nutritional component values for entered diseases:")
    print_nutritional_components(final_list)

# Execute the main function
if __name__ == "__main__":
    main()