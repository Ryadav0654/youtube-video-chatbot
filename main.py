from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from utils.transcript_extractor import extract_video_id, fetch_transcript
from rag_pipeline import split_transcript_and_store, ask_query, summarize_transcript


def main():
    st.set_page_config(page_title="Chat with YouTube Video", layout="centered")

    st.title("Chat with a YouTube Video", anchor=None, width="stretch")   
    st.write("Paste a YouTube link and ask questions about the video.")

    # Session State Init

    if "transcript" not in st.session_state:
        st.session_state.transcript = None

    if "retriever" not in st.session_state:
        st.session_state.retriever = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # URL Input
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
    )

    if st.button("Load Video"):
        video_id = extract_video_id(youtube_url)

        if not video_id:
            st.error("Invalid YouTube URL")
        else:
            st.video(youtube_url)

            with st.spinner("Fetching transcript and building knowledge base..."):
                try:
                    transcript = fetch_transcript(video_id)
                    retriever = split_transcript_and_store(transcript)

                    st.session_state.transcript = transcript
                    st.session_state.retriever = retriever
                    st.session_state.chat_history = []

                    st.success("Video loaded! You can now ask questions.")
                except Exception as e:
                    st.error(f"Failed to load video: {e}")

    # Chat Section
    if st.session_state.retriever:
        st.subheader("Chat")

        col1, col2 = st.columns([1, 3])
        with col1:
            summarize_clicked = st.button("Summarize", use_container_width=True)

        if summarize_clicked:
            with st.spinner("Summarizing the video..."):
                try:
                    summary = summarize_transcript(st.session_state.transcript)

                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": summary}
                    )

                except Exception as e:
                    st.error(f"Failed to summarize: {e}")

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_question = st.chat_input("Ask something about the video")

        if user_question:
            # Show user message
            st.session_state.chat_history.append(
                {"role": "user", "content": user_question}
            )

            with st.chat_message("user"):
                st.write(user_question)

            with st.spinner("Thinking..."):
                try:
                    answer = ask_query(
                        retriever=st.session_state.retriever, query=user_question
                    )

                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer}
                    )

                    with st.chat_message("assistant"):
                        st.write(answer)

                except Exception as e:
                    st.error(f"Failed to get answer: {e}")

    else:
        st.info("Load a YouTube video to start chatting.")


if __name__ == "__main__":
    main()
