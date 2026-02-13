import math_utils
def main():
    result = math_utils.add(5, 7)
    print(f"Result: {result}")
    return result == 12

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)