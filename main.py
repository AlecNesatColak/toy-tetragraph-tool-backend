from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "https://toy-tetragraph-hash-tool.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TransformationInput(BaseModel):
    text: str

def clean_and_uppercase(text):
    return ''.join([char.upper() for char in text if char.isalpha()])

def group_and_pad_to_matrix_with_transformations(text):
    alpha_numeric = {chr(i): i - 65 for i in range(65, 91)}
    numeric_alpha = {i - 65: chr(i) for i in range(65, 91)}
    running_total = [0, 0, 0, 0]
    detailed_steps = []

    filtered_text = clean_and_uppercase(text)
    chunks = [filtered_text[i:i+16] for i in range(0, len(filtered_text), 16)]
    padded_chunks = [chunk + 'A' * (16 - len(chunk)) for chunk in chunks]

    for chunk in padded_chunks:
        matrix = [[alpha_numeric.get(chunk[i+j*4], 0) for i in range(4)] for j in range(4)]
        alph_matrix = [[chunk[i+j*4] if i+j*4 < len(chunk) else 'A' for i in range(4)] for j in range(4)]

        step_details = {
            'original_alpha_matrix': [row[:] for row in alph_matrix],
            'original_numeric_matrix': [row[:] for row in matrix],
            'running_total_initial': running_total[:]
        }

        column_sums_initial = [sum(matrix[i][j] for i in range(4)) % 26 for j in range(4)]
        running_total = [(rt + cs) % 26 for rt, cs in zip(running_total, column_sums_initial)]

        step_details['running_total_after_initial'] = running_total[:]

        for i in range(4):
            if i < 3:
                matrix[i] = matrix[i][i+1:] + matrix[i][:i+1]
                alph_matrix[i] = alph_matrix[i][i+1:] + alph_matrix[i][:i+1]
            else:
                matrix[i].reverse()
                alph_matrix[i].reverse()

        step_details.update({
            'transformed_alpha_matrix': [row[:] for row in alph_matrix],
            'transformed_numeric_matrix': [row[:] for row in matrix],
        })

        column_sums_transformed = [sum(matrix[i][j] for i in range(4)) % 26 for j in range(4)]
        running_total = [(rt + cs) % 26 for rt, cs in zip(running_total, column_sums_transformed)]

        step_details['running_total_after_transformation'] = running_total[:]

        detailed_steps.append(step_details)

    running_total_alpha = ''.join([numeric_alpha[rt] for rt in running_total])
    return detailed_steps, running_total_alpha

@app.post("/transform/")
async def transform_text(input: TransformationInput):
    steps, final_alpha_running_total = group_and_pad_to_matrix_with_transformations(input.text)
    return {
        "steps": steps,
        "final_running_total": final_alpha_running_total
    }
