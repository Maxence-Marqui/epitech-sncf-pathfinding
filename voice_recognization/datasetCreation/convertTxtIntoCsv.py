import csv

def process_line(line):
    # Splitting the line into components
    parts = line.strip().split('|')
    
    # Extracting information from the parts
    file_name = parts[0].split('/')[1].split('.')[0]
    transcription = parts[1]
    
    # Creating a dictionary for the row
    row = {'file_name': file_name, 'normalized_transcription': transcription}
    
    return row

def main(input_file, output_file):
    # Open the input file for reading
    with open(input_file, 'r', encoding='utf-8') as file:
        # Read only the first max_rows lines from the file
        lines = file.readlines()

    # Process each line to create rows for CSV
    rows = [process_line(line) for line in lines]

    # Write to the CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        # Define the CSV columns
        fieldnames = ['file_name', 'normalized_transcription']
        
        # Create a CSV writer
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header
        csvwriter.writeheader()

        # Write the rows
        csvwriter.writerows(rows)

if __name__ == "__main__":
    # Specify the input and output file paths
    input_file_path = 'transcript.txt'
    output_file_path = 'texte.csv'

    # Call the main function with max_rows parameter
    main(input_file_path, output_file_path)

# TO do : Pas plus de 100 caractère 