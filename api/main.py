from flask import Flask, jsonify 
from flask_cors import CORS
from modules import Chord

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def hello():
    return ":3"

@app.route('/api/chord/<chord_id>', methods=['GET'])
def get_data(chord_id):
    chord = Chord.name_to_chord(chord_id)
    return jsonify({
        "id": chord.name(),
        "notes": [str(n) for n in chord.notes()],
        "intervals": [c.name() for c in chord.inversions()],
        "transpositions": [c.name() for c in chord.transpositions()],
        "extensions": [c.name() for c in chord.extensions()],
        "simplifications": [c.name() for c in chord.simplifications()],
        "subchords": {i: [c.name() for c in chords] for i, chords in chord.subchords().items()},
        "scales": chord.find_matching_scales(),
        "color": chord.color() 
    })

if __name__ == "__main__":
    app.run()
