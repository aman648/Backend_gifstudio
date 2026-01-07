# Example file: my_module.py

def main_function():
    print("This function runs when the script is executed directly.")

if __name__ == "__main__":
    main_function()
    print(f"The value of __name__ is: {__name__}")

# If this file is imported by another script, only the function definition is loaded, 
# and the code inside the if block will not run.
