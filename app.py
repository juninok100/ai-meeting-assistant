import streamlit as st

st.set_page_config(
    page_title="AI 회의 비서",
    page_icon="🎙️"
)

st.title("🎙️ AI 회의 비서")
st.write("녹음파일을 업로드하면 AI가 내용을 분석해주는 앱입니다.")

audio_file = st.file_uploader(
    "녹음파일을 업로드하세요",
    type=["mp3", "m4a", "wav", "mp4"]
)

if audio_file is not None:
    st.success(f"업로드 완료: {audio_file.name}")
    st.audio(audio_file)
