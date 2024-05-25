import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import re

def parse_xml(xml_file):
    with open(xml_file, 'r') as f:
        xml_data = f.read()
    data_start = xml_data.find('<Data>') + len('<Data>')
    data_end = xml_data.find('</Data>')
    data_section = xml_data[data_start:data_end]
    lines = data_section.split('\n')
    notes = []
    for line in lines:
        if line.strip():
            notes.append(line.strip())
    return notes

def transform_notes(notes, res):
    transformed_notes = []
    for i, note in enumerate(notes):
        time_match = re.search(r'time="([^"]+)"', note)
        duration_match = re.search(r'duration="([^"]+)"', note)
        track_match = re.search(r'track="([^"]+)"', note)
        if time_match and duration_match and track_match:
            time = float(time_match.group(1))
            duration = float(duration_match.group(1))
            track = int(track_match.group(1))
            new_time = round(time * (res * 2))
            new_duration = round(duration * (res * 2))
            transformed_notes.append(f'{new_time} = N {track} {new_duration}')
    return transformed_notes

def write_chart(transformed_notes, output_file, res):
    with open(output_file, 'w') as f:
        f.write(f"[Song]\n{{\n  Name = \"No matter what you\"\n  Artist = \"do, a freetar sng will\"\n  Charter = \"always be bad. chart\"\n  Album = \"from scratch instead.\"\n  Year = \", 2024\"\n  Offset = 0\n  Resolution = {res}\n  Player2 = bass\n  Difficulty = 2\n  PreviewStart = 0\n  PreviewEnd = 0\n  Genre = \"-Naonemeu\"\n  MediaType = \"cd\"\n}}\n")
        f.write("[SyncTrack]\n{\n  0 = TS 4\n  0 = B 120000\n}\n")
        f.write("[Events]\n{\n}\n")
        f.write("[ExpertSingle]\n{\n")
        for note in transformed_notes:
            f.write(note + '\n')
        f.write("}\n")

def convert_to_chart(xml_file, output_file):
    res = 480
    notes = parse_xml(xml_file)
    transformed_notes = transform_notes(notes, res)
    write_chart(transformed_notes, output_file, res)

def getMs(pos, bpm_array_pos, bpm_array_val, resolution, arredondar=True):
    cur_ms = 0
    for i, value in enumerate(bpm_array_pos):
        bpm = bpm_array_val[i] / 1000
        if i < len(bpm_array_pos) - 1 and pos >= bpm_array_pos[i + 1]:
            cur_ms += (((bpm_array_pos[i + 1] - bpm_array_pos[i]) / resolution) / bpm * 60)
        else:
            cur_ms += (((pos - bpm_array_pos[i]) / resolution) / bpm * 60)
            if arredondar:
                cur_ms = round(cur_ms * 24) / 24
            return cur_ms

def convert_to_sng(chart_file, arredondar=False):
    with open(chart_file, 'r', encoding='utf-8') as file1:
        lines = file1.readlines()
    sections = {}
    section_name = ""
    bpm_array_pos = []
    bpm_array_val = []
    star_power = {}

    for line in lines:
        if line.startswith('[') or line.startswith('\ufeff['):
            section_name = line[1:-2]
            if line.startswith('\ufeff['): section_name = line[2:-2]
        if '=' in line:
            split = line.split('=')
            if section_name not in sections and section_name != "SyncTrack":
                sections[section_name] = {}
            split_key = split[0].strip()
            split_value = split[1].strip()
            if section_name == "Song":
                if split_value.startswith("\""):
                    split_value = split_value[1:-1]
                sections[section_name][split_key] = split_value
            elif section_name == "SyncTrack":
                if "TS" not in split_value:
                    bpm_array_pos.append(int(split_key))
                    bpm_array_val.append(int(split_value[2:].strip()))
            elif section_name == "ExpertSingle":
                if split_key not in sections[section_name]:
                    sections[section_name][split_key] = []
                sections[section_name][split_key].append(split_value)
                if split_value.startswith("S 2"):
                    sp_split = split_value.split(' ')
                    star_power[split_key] = sp_split[2]
    

    offset = float(sections["Song"]["Offset"])
    resolution = int(sections["Song"]["Resolution"])
    length = list(sections["ExpertSingle"].keys())[-1]
    last_note_dur = 0
    for dur in sections["ExpertSingle"][length]:
        if not dur.startswith("N 5") and not dur.startswith("N 6"):
            end_tick = int(length)
            if dur.startswith("N"):
                end_tick = int(length) + (int(dur.split(' ')[2]))
            pos = round(getMs(int(end_tick), bpm_array_pos, bpm_array_val, resolution, arredondar) + offset + 3, 3)
            if pos > last_note_dur:
                last_note_dur = pos
    length = last_note_dur

    bps = "24.0"

    out = """<?xml version="1.0"?>
<Song>
    <Properties>
        <Version>0.1</Version>
        <Title>{}</Title>
        <Artist>{}</Artist>
        <Album>No Album Set</Album>
        <Year>0</Year>
        <BeatsPerSecond>{}</BeatsPerSecond>
        <BeatOffset>0.0</BeatOffset>
        <HammerOnTime>0.25</HammerOnTime>
        <PullOffTime>0.25</PullOffTime>
        <Difficulty>EXPERT</Difficulty>
        <AllowableErrorTime>0.05</AllowableErrorTime>
        <Length>{}</Length>
        <MusicFileName>{}</MusicFileName>
        <MusicDirectoryHint>./</MusicDirectoryHint>
    </Properties>

    <Data>
""".format(sections["Song"]["Name"], sections["Song"]["Artist"], bps, str(length), sections["Song"]["MusicStream"])

    for key, value in sections["ExpertSingle"].items():
        for note_str in value:
            if note_str.startswith("N") and not note_str.startswith("N 5") and not note_str.startswith("N 6"):
                split = note_str.split(' ')
                note = split[1]
                if note == '7':
                    note = '0'
                start_tick = int(key)
                end_tick = start_tick + (int(split[2]))
                pos = getMs(start_tick, bpm_array_pos, bpm_array_val, resolution, arredondar)
                duration = getMs(end_tick, bpm_array_pos, bpm_array_val, resolution, arredondar) - pos
                if duration < 0.25:
                    duration = 0.0
                special = 0
                for key2, value2 in star_power.items():
                    sp_start_tick = int(key2)
                    if sp_start_tick > start_tick:
                        continue
                    if start_tick >= sp_start_tick and start_tick < sp_start_tick + int(value2):
                        special = 1
                out += '        <Note time="{}" duration="{}" track="{}" special="{}" />\n'.format(
                    round(pos + offset, 6), round(duration, 6), note, special)

    out += """    </Data>
</Song>"""

    out_path = chart_file + '.ExpertSingle.sng'
    with open(out_path, "w", encoding='utf-8') as text_file:
        text_file.write(out)
    return out_path


def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        return file_path
    else:
        messagebox.showerror("Erro", "Nenhum arquivo selecionado")
        return None

def convert_chart_to_sng():
    file_path = select_file()
    if file_path:
        arredondar = messagebox.askyesno("Arredondar para 24 bps", "Você deseja arredondar para 24 bps?")
        output_path = convert_to_sng(file_path, arredondar)
        messagebox.showinfo("Sucesso", f"Arquivo convertido e salvo em: {output_path}")
    

def convert_sng_to_chart():
    file_path = select_file()
    if file_path:
        output_file = filedialog.asksaveasfilename(defaultextension=".chart", filetypes=[("Chart files", "*.chart")])
        if output_file:
            convert_to_chart(file_path, output_file)
            messagebox.showinfo("Sucesso", f"Arquivo convertido e salvo em: {output_file}")

# Criar janela principal
root = tk.Tk()
root.title("Conversor de Arquivos Chart/SNG")
root.geometry("400x200")

# Estilo
style = ttk.Style(root)

# Verificar temas disponíveis e aplicar um tema padrão
available_themes = style.theme_names()
default_theme = "clam" if "clam" in available_themes else available_themes[0]
style.theme_use(default_theme)

# Frame principal
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(expand=True, fill=tk.BOTH)

# Título
title_label = ttk.Label(main_frame, text="Conversor de Arquivos Chart/SNG", font=("Helvetica", 16, "bold"))
title_label.pack(pady=10)

# Criar botões
btn_chart_to_sng = ttk.Button(main_frame, text="Converter .chart para .sng", command=convert_chart_to_sng)
btn_chart_to_sng.pack(pady=10)

btn_sng_to_chart = ttk.Button(main_frame, text="Converter .sng para .chart", command=convert_sng_to_chart)
btn_sng_to_chart.pack(pady=10)

# Executar a aplicação
root.mainloop()