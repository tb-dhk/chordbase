import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import Vex, { Accidental } from "vexflow";
import { sha256 } from 'js-sha256'

function getColor(chord) {
  const hexColor = "#" + sha256(chord).slice(0, 6);  // Get first 6 characters of the SHA-256 hash

  // Convert hex to RGB
  let r = parseInt(hexColor.slice(1, 3), 16);
  let g = parseInt(hexColor.slice(3, 5), 16);
  let b = parseInt(hexColor.slice(5, 7), 16);

  // Normalize RGB to [0, 1]
  r /= 255;
  g /= 255;
  b /= 255;

  // Convert RGB to HSV
  let max = Math.max(r, g, b);
  let min = Math.min(r, g, b);
  let h = 0;
  let s = max === 0 ? 0 : (max - min) / max;
  let v = max;

  if (max !== min) {
    if (max === r) {
      h = (g - b) / (max - min);
    } else if (max === g) {
      h = 2 + (b - r) / (max - min);
    } else {
      h = 4 + (r - g) / (max - min);
    }
  }

  h = (h * 60) % 360;
  if (h < 0) h += 360;

  // Double the brightness and saturation, ensuring they don't exceed 1
  s = Math.min(s * 2, 1);
  v = Math.min(v * 2, 1);

  // Convert back to RGB
  let c = v * s;
  let x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  let m = v - c;

  let rp, gp, bp;
  if (h >= 0 && h < 60) {
    rp = c; gp = x; bp = 0;
  } else if (h >= 60 && h < 120) {
    rp = x; gp = c; bp = 0;
  } else if (h >= 120 && h < 180) {
    rp = 0; gp = c; bp = x;
  } else if (h >= 180 && h < 240) {
    rp = 0; gp = x; bp = c;
  } else if (h >= 240 && h < 300) {
    rp = x; gp = 0; bp = c;
  } else {
    rp = c; gp = 0; bp = x;
  }

  // Normalize RGB values to [0, 255]
  r = Math.round((rp + m) * 255);
  g = Math.round((gp + m) * 255);
  b = Math.round((bp + m) * 255);

  // Convert RGB back to hex
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

function formatChordID(name) {
  if (name) {
    const parts = name.split('^');
    if (parts.length > 1) {
      return (
        <>
          {parts[0]}<sup>{parts[1]}</sup>
        </>
      );
    }
    return name;
  }
};

// Helper function to convert notes to VexFlow format
const convertNotesToVexFlow = (notes) => {
  return notes.map((note) => {
    const [_, pitch, accidental, octave] = note.match(/^([A-G])([#b]*)(\d+)$/) || [];
    if (!pitch || !octave) {
      console.error(`Invalid note format: ${note}`);
      return null;
    }

    // Convert to VexFlow format
    const vexPitch = pitch.toLowerCase();
    return `${vexPitch}${accidental}/${octave}`;
  }).filter(Boolean); // Remove nulls in case of invalid notes
};

function ChordSVG({ chordIDs, highlight, endsOnly }) {
  const [chordNotes, setChordNotes] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [colors, setColors] = useState([])
  const svgContainerRef = useRef(null); // Reference for the SVG container

  useEffect(() => {
    // Fetch chord data for each chordID
    async function fetchInfo (origin, array, key, eo) {
      try {
        const promises = origin.map((chordID) =>
          fetch(`/api/chord/${encodeURIComponent(chordID)}`).then((response) =>
            response.json()
          )
        );
        const chordData = await Promise.all(promises);
        var vexNotes = chordData.map((data) => (data[key]))
        if (key === "notes") {
          vexNotes = vexNotes.map(notes => convertNotesToVexFlow(eo ? [notes[0], notes[notes.length - 1]] : notes)); // Convert each chord's notes to VexFlow format
        }
        array(vexNotes);
      } catch (error) {
        console.error("Error fetching chord data:", error);
      }
    };

    if (chordIDs) {
      fetchInfo(chordIDs, setChordNotes, "notes");
    }
    if (highlight) {
      fetchInfo(highlight, setHighlights, "notes", endsOnly);
      setColors(highlight.map(chord => getColor(chord)))
    }
  }, [chordIDs]);
  
  useEffect(() => {
    if (chordNotes.length > 0 && svgContainerRef.current) {
      // Clear previous SVG content
      svgContainerRef.current.innerHTML = "";

      // VexFlow setup
      const VF = Vex.Flow;
      const renderer = new VF.Renderer(svgContainerRef.current, VF.Renderer.Backends.SVG);
      renderer.resize(150 + chordNotes.length * 100, 150); // Adjust width based on the number of chords
      const context = renderer.getContext();

      // Create a stave
      const stave = new VF.Stave(10, 10, 130 + chordNotes.length * 100); // Extend stave width for all chords
      stave.setStyle({ strokeStyle: "white", fillStyle: "white" });
      stave.setContext(context).draw();

      const clef = stave.addClef("treble");
      clef.setStyle({ fillStyle: 'white', strokeStyle: 'white' });
      clef.drawWithStyle()
      
      // Map each chord to a set of StaveNotes and format them
      const staveNotes = chordNotes.map((notes, index) => {
        // Create StaveNotes for each chord
        const note = new VF.StaveNote({
          keys: notes,
          duration: "w", // Whole note duration
        });

        // Set default styles for the note
        note.setStyle({ strokeStyle: "white", fillStyle: "white" });
        note.setLedgerLineStyle({ fillStyle: "white", strokeStyle: "white" });

        // Highlight the notes if they are in the highlights for the current chord
        notes.forEach((noteKey, noteindex) => {
          // Check if the note is in the highlights list
          if (highlights[index] && highlights[index].includes(noteKey)) {
            const color = colors[index]; // Get the color for the current chord
            note.setKeyStyle(noteindex, { strokeStyle: color, fillStyle: color });
          }
        });

        return note;
      });

      // Create a voice for the notes
      const voice = new VF.Voice({ num_beats: 4 * chordNotes.length, beat_value: 4 });
      voice.addTickables(staveNotes);
      Accidental.applyAccidentals([voice], "C")

      // Format and render the voice
      new VF.Formatter().joinVoices([voice]).format([voice], stave.getWidth() - 40);
      voice.draw(context, stave);
    }
  }, [chordNotes]);

  return (
    <div className="svg-container">
      <div ref={svgContainerRef} className="svg"></div>
      {chordNotes.length === 0 && <p></p>}
    </div>
  );
}

function Chord() {
  const { id } = useParams();  // Access the dynamic route parameter
  const [chordInfo, setChordInfo] = useState(null);
  const [interval, setInterval] = useState(0);
  const [subchords, setSubchords] = useState([])
  const [scales, setScales] = useState([])

  useEffect(() => {
    fetch(`/api/chord/${encodeURIComponent(id)}`)
      .then((response) => response.json())
      .then((data) => setChordInfo(data))
      .catch((error) => console.error('Error fetching chord data:', error));
    if (chordInfo) {
      setInterval(Object.keys(chordInfo.intervals)[0])
    }
  }, [id]);

  useEffect(() => {
    if (chordInfo) {
      setSubchords(chordInfo.subchords[interval] || [])
      setScales(chordInfo.scales['1.0'] ? chordInfo.scales['1.0'] : [])
    }
  }, [interval])

  function offsetIntervals(num) {
    const intervals = Object.keys(chordInfo.intervals).sort();
    
    // Check if interval exists in the list, otherwise find the nearest one
    let index = intervals.indexOf(interval);
    
    // If interval is not found, find the nearest valid interval
    if (index === -1) {
      // Find the closest interval based on the direction of num (positive or negative)
      index = intervals.reduce((closestIndex, currentInterval, currentIndex) => {
        // Compare distance between intervals
        const currentDistance = Math.abs(intervals[currentIndex] - interval);
        const closestDistance = Math.abs(intervals[closestIndex] - interval);
        return currentDistance < closestDistance ? currentIndex : closestIndex;
      }, 0); // Default to the first interval if no better match is found
    }

    // Offset and wrap around using modulo
    return intervals[(index + num) % intervals.length];
  }

  if (!chordInfo) {
    return <div>loading...</div>;
  }

  return (
    <div className="body">
      <h1>{formatChordID(chordInfo.id)}</h1>
      <p style={{color: "#888"}}>({chordInfo.notes.join(", ")})</p>
      <ChordSVG chordIDs={[chordInfo.id]} />

      <div className="half-grid">
        <div>
          <h3>simplifications:</h3>
          {chordInfo.simplifications.map((chord, index) => (
            <Link to={`/chord/${encodeURIComponent(chord)}`}>
              <div key={index} className="chord">
                <p>{formatChordID(chord)}</p>
                <ChordSVG chordIDs={[chord]} />
              </div>
            </Link>
          ))}
        </div>

        <div>
          <h3>extensions:</h3>
          {chordInfo.extensions.map((chord, index) => (
            <Link to={`/chord/${encodeURIComponent(chord)}`}>
              <div key={index} className="chord">
                <p>{formatChordID(chord)}</p>
                <ChordSVG chordIDs={[chord]} />
              </div>
            </Link>
          ))}
        </div>
      </div>

      <h3>scales:</h3>
      <ul>
        {scales.map((scale, index) => (
          <li key={index}>
            {scale} 
          </li>
        ))}
      </ul>

      <div>
        <h3>interval and subchord size:</h3>
        <button>-</button>
        <input type="text" onChange={
          e => {
            if (e.target.value) {
              setInterval(parseInt(e.target.value))
            }
          }
        } />
        <button>+</button>
      </div>

      <div className="half-grid">
        <div>
          <h3>intervals:</h3>
          <div>
            <ChordSVG 
              chordIDs={new Array(subchords.length).fill(chordInfo.id)} 
              highlight={subchords} 
              endsOnly={true}
            />
          </div>
        </div>

        <div>
          <h3>subchords:</h3>
          <div>
            <ChordSVG 
              chordIDs={new Array(subchords.length).fill(chordInfo.id)} 
              highlight={subchords} 
          />
          </div>
        </div>
      </div>

      <h3>transpositions:</h3>
      <ul>
        <ChordSVG chordIDs={chordInfo.transpositions} />
      </ul>
    </div>
  );
}

export default Chord;
