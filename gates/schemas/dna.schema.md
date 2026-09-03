# DNA.json — обязательные поля (проверяет gates/stage1.py)
duration_s, width, height, fps, orientation, source{file, measured_by, measured_at, live_measurement:bool}
scenes[] {i, start, end, len}  — покрытие 100% таймлайна
cuts{n, avg_len, median_len, cuts_per_min, sigma, under3s, by_act[]}
speech{mode: sung|spoken, words, wpm, wps, language, segments, pauses}
audio{bpm, lufs, has_bed:bool}
captions{style, count, per_min, median_hold, karaoke:bool, position}
beats[] {id, start, end, pct_from, pct_to, role∈{hook,problem,agitate,mechanism,proof,transformation,offer,price,urgency,callback,cta,cutaway,backstory,mentor,diagnosis,handover,resolution,brand}, in_frame, belief}
sale_starts_s, enemy{object, n_shots}, audio_route∈{suno-first, vo+bed}
