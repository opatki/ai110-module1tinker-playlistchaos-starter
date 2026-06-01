import streamlit as st

from playlist_logic import (
    DEFAULT_PROFILE,
    Song,
    build_playlists,
    compute_playlist_stats,
    history_summary,
    lucky_pick,
    merge_playlists,
    normalize_song,
    search_songs,
)

GENRE_OPTIONS = ["rock", "lofi", "pop", "jazz", "electronic", "ambient", "other"]


def init_state():
    """Initialize Streamlit session state."""
    if "songs" not in st.session_state:
        st.session_state.songs = default_songs()
    if "profile" not in st.session_state:
        st.session_state.profile = dict(DEFAULT_PROFILE)
    if "history" not in st.session_state:
        st.session_state.history = []


def default_songs():
    """Return a default list of songs."""
    # (title, artist, genre, energy, tags)
    data = [
        ("Thunderstruck", "AC/DC", "rock", 9, ["classic", "guitar"]),
        ("Lo-fi Rain", "DJ Calm", "lofi", 2, ["study"]),
        ("Night Drive", "Neon Echo", "electronic", 6, ["synth"]),
        ("Soft Piano", "Sleep Sound", "ambient", 1, ["sleep"]),
        ("Bohemian Rhapsody", "Queen", "rock", 8, ["classic", "opera"]),
        ("Blinding Lights", "The Weeknd", "pop", 8, ["synth", "dance"]),
        ("Take Five", "Dave Brubeck", "jazz", 4, ["classic", "instrumental"]),
        ("Strobe", "Deadmau5", "electronic", 7, ["progressive", "long"]),
        ("Weightless", "Marconi Union", "ambient", 1, ["relax", "sleep"]),
        ("Smells Like Teen Spirit", "Nirvana", "rock", 9, ["grunge", "90s"]),
        ("Levitating", "Dua Lipa", "pop", 8, ["dance", "party"]),
        ("So What", "Miles Davis", "jazz", 3, ["trumpet", "cool"]),
        ("Midnight City", "M83", "electronic", 7, ["indie", "dream"]),
        ("Gymnopedie No.1", "Erik Satie", "ambient", 1, ["piano", "calm"]),
        ("Sweet Child O' Mine", "Guns N' Roses", "rock", 8, ["guitar", "80s"]),
        ("Bad Guy", "Billie Eilish", "pop", 6, ["bass", "dark"]),
        ("Fly Me to the Moon", "Frank Sinatra", "jazz", 5, ["vocal", "swing"]),
        ("Sandstorm", "Darude", "electronic", 10, ["trance", "meme"]),
        ("Clair de Lune", "Claude Debussy", "ambient", 2, ["piano", "classical"]),
        ("Hotel California", "Eagles", "rock", 6, ["classic", "guitar"]),
        ("Uptown Funk", "Mark Ronson ft. Bruno Mars", "pop", 9, ["funk", "dance"]),
        ("Feeling Good", "Nina Simone", "jazz", 6, ["soul", "vocal"]),
    ]
    return [
        {"title": title, "artist": artist, "genre": genre, "energy": energy, "tags": tags}
        for title, artist, genre, energy, tags in data
    ]


def profile_sidebar():
    """Render and update the user profile."""
    st.sidebar.header("Mood profile")

    profile = st.session_state.profile

    profile["name"] = st.sidebar.text_input(
        "Profile name",
        value=str(profile.get("name", "")),
    )

    # (profile key, label, default) for the two energy-threshold sliders.
    energy_sliders = [
        ("hype_min_energy", "Hype min energy", 7),
        ("chill_max_energy", "Chill max energy", 3),
    ]
    for col, (key, label, default) in zip(st.sidebar.columns(2), energy_sliders):
        with col:
            profile[key] = st.sidebar.slider(
                label,
                min_value=1,
                max_value=10,
                value=int(profile.get(key, default)),
            )

    profile["favorite_genre"] = st.sidebar.selectbox(
        "Favorite genre",
        options=GENRE_OPTIONS,
        index=0,
    )

    profile["include_mixed"] = st.sidebar.checkbox(
        "Include Mixed playlist in views",
        value=bool(profile.get("include_mixed", True)),
    )

    st.sidebar.write("Current profile:", profile["name"])


def add_song_sidebar():
    """Render the Add Song controls in the sidebar."""
    st.sidebar.header("Add a song")

    title = st.sidebar.text_input("Title")
    artist = st.sidebar.text_input("Artist")
    genre = st.sidebar.selectbox(
        "Genre",
        options=GENRE_OPTIONS,
    )
    energy = st.sidebar.slider("Energy", min_value=1, max_value=10, value=5)
    tags_text = st.sidebar.text_input("Tags (comma separated)")

    if st.sidebar.button("Add to playlist"):
        raw_tags = [t.strip() for t in tags_text.split(",")]
        tags = [t for t in raw_tags if t]

        song: Song = {
            "title": title,
            "artist": artist,
            "genre": genre,
            "energy": energy,
            "tags": tags,
        }
        if title and artist:
            normalized = normalize_song(song)
            all_songs = st.session_state.songs[:]
            all_songs.append(normalized)
            st.session_state.songs = all_songs


def playlist_tabs(playlists):
    """Render playlists in tabs."""
    include_mixed = st.session_state.profile.get("include_mixed", True)

    tab_labels = ["Hype", "Chill"]
    if include_mixed:
        tab_labels.append("Mixed")

    tabs = st.tabs(tab_labels)

    for label, tab in zip(tab_labels, tabs):
        with tab:
            render_playlist(label, playlists.get(label, []))


def render_playlist(label, songs):
    st.subheader(f"{label} playlist")
    if not songs:
        st.write("No songs in this playlist.")
        return

    query = st.text_input(f"Search {label} playlist by artist", key=f"search_{label}")
    filtered = search_songs(songs, query, field="artist")

    if not filtered:
        st.write("No matching songs.")
        return

    for song in filtered:
        mood = song.get("mood", "?")
        tags = ", ".join(song.get("tags", []))
        st.write(
            f"- **{song['title']}** by {song['artist']} "
            f"(genre {song['genre']}, energy {song['energy']}, mood {mood}) "
            f"[{tags}]"
        )


def lucky_section(playlists):
    """Render the lucky pick controls and result."""
    st.header("Lucky pick")

    mode = st.selectbox(
        "Pick from",
        options=["any", "hype", "chill"],
        index=0,
    )

    if st.button("Feeling lucky"):
        pick = lucky_pick(playlists, mode=mode)
        if pick is None:
            st.warning("No songs available for this mode.")
            return

        st.success(
            f"Lucky song: {pick['title']} by {pick['artist']} "
            f"(mood {pick.get('mood', '?')})"
        )

        history = st.session_state.history
        history.append(pick)
        st.session_state.history = history


def stats_section(playlists):
    """Render statistics based on the playlists."""
    st.header("Playlist stats")

    stats = compute_playlist_stats(playlists)

    metrics = [
        ("Total songs", stats["total_songs"]),
        ("Hype songs", stats["hype_count"]),
        ("Chill songs", stats["chill_count"]),
        ("Mixed songs", stats["mixed_count"]),
        ("Hype ratio", f"{stats['hype_ratio']:.2f}"),
        ("Average energy", f"{stats['avg_energy']:.2f}"),
    ]

    # Render the metrics three per row.
    for start in range(0, len(metrics), 3):
        row = metrics[start:start + 3]
        for col, (label, value) in zip(st.columns(3), row):
            col.metric(label, value)

    top_artist = stats["top_artist"]
    if top_artist:
        st.write(
            f"Most common artist: {top_artist} "
            f"({stats['top_artist_count']} songs)"
        )
    else:
        st.write("No top artist yet.")


def history_section():
    """Render the pick history overview."""
    st.header("History")

    history = st.session_state.history
    if not history:
        st.write("No history yet.")
        return

    summary = history_summary(history)
    st.write("Recent picks by mood:", summary)

    show_details = st.checkbox("Show full history")
    if show_details:
        for song in history:
            st.write(
                f"{song.get('mood', '?')}: {song['title']} by {song['artist']}"
            )


def clear_controls():
    """Render a small section for clearing data."""
    st.sidebar.header("Manage data")
    if st.sidebar.button("Reset songs to default"):
        st.session_state.songs = default_songs()
    if st.sidebar.button("Clear history"):
        st.session_state.history = []


def main():
    st.set_page_config(page_title="Playlist Chaos", layout="wide")
    st.title("Playlist Chaos")

    st.write(
        "An AI assistant tried to build a smart playlist engine. "
        "The code runs, but the behavior is a bit unpredictable."
    )

    init_state()
    profile_sidebar()
    add_song_sidebar()
    clear_controls()

    profile = st.session_state.profile
    songs = st.session_state.songs

    playlists = merge_playlists(build_playlists(songs, profile), {})

    # Each playlist section is followed by a divider, then the history view.
    for render_section in (playlist_tabs, lucky_section, stats_section):
        render_section(playlists)
        st.divider()
    history_section()


if __name__ == "__main__":
    main()
