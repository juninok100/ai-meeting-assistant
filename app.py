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
st.write("녹음파일을 업로드하면 녹취하고 AI가 내용을 정리합니다.")


# -------------------------
# Whisper 모델 불러오기
# -------------------------
@st.cache_resource
def load_whisper_model():
    return WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )


# -------------------------
# 저장 공간
# -------------------------
if "transcript" not in st.session_state:
    st.session_state.transcript = ""

if "analysis" not in st.session_state:
    st.session_state.analysis = ""

if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = ""


# -------------------------
# 녹음파일 업로드
# -------------------------
audio_file = st.file_uploader(
    "녹음파일을 업로드하세요",
    type=["mp3", "m4a", "wav", "mp4"]
)


if audio_file is not None:

    # 새로운 파일이면 이전 결과 초기화
    if st.session_state.uploaded_name != audio_file.name:
        st.session_state.uploaded_name = audio_file.name
        st.session_state.transcript = ""
        st.session_state.analysis = ""

    st.success(f"업로드 완료: {audio_file.name}")

    st.audio(audio_file)


    # -------------------------
    # 음성 → 텍스트
    # -------------------------
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

                model = load_whisper_model()

                segments, info = model.transcribe(
                    temp_path,
                    language=None
                )

                transcript = ""

                for segment in segments:
                    transcript += segment.text.strip() + "\n"

                st.session_state.transcript = transcript

            except Exception as e:

                st.error("음성 변환 중 오류가 발생했습니다.")
                st.error(str(e))

            finally:

                if os.path.exists(temp_path):
                    os.remove(temp_path)


# -------------------------
# 녹취 결과 표시
# -------------------------
if st.session_state.transcript:

    st.subheader("📄 녹취 결과")

    st.text_area(
        "변환된 텍스트",
        st.session_state.transcript,
        height=350
    )


    # -------------------------
    # Gemini AI 분석
    # -------------------------
    if st.button("🤖 AI 분석하기"):

        with st.spinner("AI가 회의 내용을 분석하고 있습니다..."):

            try:

                client = genai.Client(
                    api_key=st.secrets["GEMINI_API_KEY"]
                )

                prompt = f"""
너는 전문 회의 비서다.

아래 녹취 내용을 읽고 회의 결과를 한국어로 깔끔하게 정리해라.

중요한 규칙:
- 녹취록에 없는 내용은 추측하지 마라.
- 담당자나 기한이 명확하지 않으면 "미정"이라고 표시해라.
- 중요한 내용은 빠뜨리지 마라.
- 불필요한 반복이나 잡담은 제외해라.
- 업무에 바로 활용할 수 있도록 간결하게 정리해라.

다음 형식으로 작성해라.

# 📌 한 줄 요약
회의 전체 내용을 한 문장으로 요약

# 📝 회의 요약
전체 내용을 이해하기 쉽게 요약

# 🔑 핵심 논의사항
- 주요 논의 내용

# ✅ 결정사항
- 최종적으로 결정된 내용
- 결정사항이 없으면 "없음"

# 📋 해야 할 일
- 업무:
  - 담당자:
  - 기한:

# ❓ 추가 확인사항
- 아직 결정되지 않았거나 추가 확인이 필요한 내용

--------------------

[녹취록]

{st.session_state.transcript}
"""

                response = client.interactions.create(
                    model="gemini-3.7-flash",
                    input=prompt
                )

                st.session_state.analysis = response.output_text

            except Exception as e:

                st.error("AI 분석 중 오류가 발생했습니다.")
                st.error(str(e))


# -------------------------
# AI 분석 결과
# -------------------------
if st.session_state.analysis:

    st.divider()

    st.subheader("🤖 AI 회의 분석")

    st.markdown(st.session_state.analysis)
