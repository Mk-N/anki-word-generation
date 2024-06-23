import requests

def get_random_words(length):
    url = "https://random-word-api.herokuapp.com/word"
    response = requests.get(f"{url}?number={length}")
    if response.status_code == 200:
        return response.json()
    else:
        return []

def get_word_definition(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def main():
    num_words = int(input("Enter the number of random words: "))
    random_words = get_random_words(num_words)

    for word in random_words:
        print(f"\nWord: {word}")
        definitions = get_word_definition(word)

        if definitions:
            for meaning in definitions[0].get('meanings', []):
                part_of_speech = meaning.get('partOfSpeech')
                print(f"\nType: {part_of_speech.capitalize()}")

                for definition in meaning.get('definitions', []):
                    definition_text = definition.get('definition')
                    example = definition.get('example')
                    if example:
                        print(f"Definition: {definition_text}\nExample: {example}")
                    else:
                        print(f"Definition: {definition_text}")
        else:
            print("Definition not found.")

if __name__ == "__main__":
    main()
