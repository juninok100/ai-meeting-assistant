import streamlit as st
import tempfile
import os

from faster_whisper import WhisperModel
from google import genai


st.set_page_config(
    page_title="AI 회의 비서",
    page_icon="🎙️"
)

st.title("🎙️ AI 회의 비서")
st.write("녹음파일을 올리면 AI가 자동으로 녹취하고 내용을 분석합니다.")


# Whisper 모델
@st.cache_resource
def load_whisper_model():
    return WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )


# 결과 저장
if "transcript" not in st.session_state:
    st.session_state.transcript = ""

if "analysis" not in st.session_state:
    st.session_state.analysis = ""

if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = ""


# 파일 업로드
audio_file = st.file_uploader(
    "🎧 녹음파일을 업로드하세요",
    type=["mp3", "m4a", "wav", "mp4"]
)


if audio_file is not None:

    if st.session_state.uploaded_name != audio_file.name:
        st.session_state.uploaded_name = audio_file.name
        st.session_state.transcript = ""
        st.session_state.analysis = ""

    st.success(f"업로드 완료: {audio_file.name}")

    st.audio(audio_file)

    # 한 번에 전체 분석
    if st.button("🚀 녹음 분석 시작", type="primary"):

        file_extension = os.path.splitext(audio_file.name)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp_file:

            temp_file.write(audio_file.getbuffer())
            temp_path = temp_file.name

        try:

            # 1. 음성 → 텍스트
            with st.spinner("① 녹음 내용을 글자로 변환하고 있습니다..."):

                model = load_whisper_model()

                segments, info = model.transcribe(
                    temp_path,
                    language=None
                )

                transcript = ""

                for segment in segments:
                    transcript += segment.text.strip() + "\n"

                st.session_state.transcript = transcript


            # 2. Gemini 분석
            with st.spinner("② AI가 내용을 분석하고 있습니다..."):

                client = genai.Client(
                    api_key=st.secrets["GEMINI_API_KEY"]
                )

                prompt = f"""
너는 전문적인 AI 회의 비서다.

아래 녹취록을 읽고 업무에 바로 사용할 수 있도록 정리해라.

규칙:
- 녹취록에 없는 내용은 절대로 추측하지 않는다.
- 불필요한 반복과 잡담은 제외한다.
- 담당자가 명확하지 않으면 "미정"으로 표시한다.
- 기한이 명확하지 않으면 "미정"으로 표시한다.
- 중요한 결정사항과 해야 할 일을 빠뜨리지 않는다.

다음 형식으로 작성해라.

# 📌 한 줄 요약
회의 내용을 한 문장으로 요약

# 📝 전체 요약
회의 내용을 이해하기 쉽게 정리

# 🔑 핵심 논의사항
- 주요 논의사항을 항목별로 작성

# ✅ 결정사항
- 최종적으로 결정된 내용
- 없으면 "없음"

# 📋 해야 할 일
각 업무별로 아래 형식으로 작성

- 업무:
- 담당자:
- 기한:

# ❓ 추가 확인사항
- 아직 결정되지 않은 사항
- 추가로 확인해야 할 사항
- 없으면 "없음"


[녹취록]

{st.session_state.transcript}
"""

                response = client.interactions.create(
                    model="gemini-3.7-flash",
                    input=prompt
                )

                st.session_state.analysis = response.output_text

        except Exception as e:

            st.error("처리 중 오류가 발생했습니다.")
            st.error(str(e))

        finally:

            if os.path.exists(temp_path):
                os.remove(temp_path)


# 녹취록 표시
if st.session_state.transcript:

    st.divider()

    st.subheader("📄 전체 녹취록")

    st.text_area(
        "녹취 내용",
        st.session_state.transcript,
        height=300
    )


# 분석 결과 표시
if st.session_state.analysis:

    st.divider()

    st.subheader("🤖 AI 분석 결과")

    st.markdown(st.session_state.analysis)
