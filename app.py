import streamlit as st
import tempfile
import os

from faster_whisper import WhisperModel


st.set_page_config(
    page_title="AI 회의 비서",
    page_icon="🎙️"
)

st.title("🎙️ AI 회의 비서")
st.write("녹음파일을 업로드하면 음성을 텍스트로 변환합니다.")


# Whisper 모델은 한 번만 불러오기
@st.cache_resource
def load_model():
    return WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )


audio_file = st.file_uploader(
    "녹음파일을 업로드하세요",
    type=["mp3", "m4a", "wav", "mp4"]
)


if audio_file is not None:

    st.success(f"업로드 완료: {audio_file.name}")

    st.audio(audio_file)

    if st.button("📝 텍스트로 변환하기"):

        with st.spinner("녹음 내용을 텍스트로 변환하고 있습니다..."):

            file_extension = os.path.splitext(audio_file.name)[1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_extension
            ) as temp_file:

                temp_file.write(audio_file.getbuffer())
                temp_path = temp_file.name

            try:

                model = load_model()

                segments, info = model.transcribe(
                    temp_path,
                    language=None
                )

                transcript = ""

                for segment in segments:
                    transcript += segment.text.strip() + "\n"

                st.subheader("📄 녹취 결과")

                st.text_area(
                    "변환된 텍스트",
                    transcript,
                    height=400
                )

            except Exception as e:

                st.error("음성 변환 중 오류가 발생했습니다.")
                st.error(str(e))

            finally:

                if os.path.exists(temp_path):
                    os.remove(temp_path)
