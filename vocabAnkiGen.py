import os
import requests
import time
import concurrent.futures
import csv

# Rate limit settings
REQUESTS_PER_MINUTE = 60
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE

def get_random_words(length):
    url = "https://random-word-api.herokuapp.com/word"
    response = requests.get(f"{url}?number={length}")
    if response.status_code == 200:
        return response.json()
    else:
        return []

def get_word_definition(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print("Rate limit exceeded, waiting before retrying...")
                time.sleep(DELAY_BETWEEN_REQUESTS)
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, retrying...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

def save_to_file(content, csv_content):
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    text_file_path = os.path.join(output_dir, 'random_words_definitions.txt')
    with open(text_file_path, 'w') as file:
        file.write(content)

    csv_file_path = os.path.join(output_dir, 'random_words_definitions.csv')
    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Word Name", "Word Type", "Definition", "Hint"])
        writer.writerows(csv_content)

def main():
    num_words = int(input("Enter the number of random words: "))
    collected_words = set()
    output_content = ""
    csv_content = []
    remaining_words = num_words

    while remaining_words > 0:
        random_words = get_random_words(remaining_words)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(1000, remaining_words)) as executor:
            futures = {executor.submit(get_word_definition, word): word for word in random_words}
            for future in concurrent.futures.as_completed(futures):
                word = futures[future]
                definitions = future.result()
                if definitions:
                    collected_words.add(word)
                    output_content += f"\nWord: {word}\n"
                    for meaning in definitions[0].get('meanings', []):
                        part_of_speech = meaning.get('partOfSpeech')
                        output_content += f"\nType: {part_of_speech.capitalize()}\n"

                        for definition in meaning.get('definitions', []):
                            definition_text = definition.get('definition')
                            example = definition.get('example')
                            if example:
                                output_content += f"Definition: {definition_text}\nExample: {example}\n"
                            else:
                                output_content += f"Definition: {definition_text}\n"
                            csv_content.append([word, part_of_speech.capitalize(), definition_text, ""])
                else:
                    print(f"No definition found for word: {word}")

                # Rate limiting
                time.sleep(DELAY_BETWEEN_REQUESTS)

        remaining_words = num_words - len(collected_words)

    if output_content:
        save_to_file(output_content, csv_content)
        print(f"Definitions have been saved to 'output/random_words_definitions.txt' and 'output/random_words_definitions.csv'. Total words collected: {len(collected_words)}")
    else:
        print("No valid definitions were found.")

if __name__ == "__main__":
    main()
