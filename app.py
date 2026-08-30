import streamlit as st
import tempfile
import os
import mimetypes

from google import genai


st.set_page_config(
    page_title="AI 회의 비서",
    page_icon="🎙️"
)

st.title("🎙️ AI 회의 비서")
st.write("녹음파일을 올리면 AI가 녹취하고 회의 내용을 자동으로 정리합니다.")


# 결과 저장
if "result" not in st.session_state:
    st.session_state.result = ""

if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = ""


# 녹음파일 업로드
audio_file = st.file_uploader(
    "🎧 녹음파일을 업로드하세요",
    type=["mp3", "m4a", "wav", "mp4"]
)


if audio_file is not None:

    # 새 파일을 올리면 이전 분석 결과 삭제
    if st.session_state.uploaded_name != audio_file.name:
        st.session_state.uploaded_name = audio_file.name
        st.session_state.result = ""

    st.success(f"업로드 완료: {audio_file.name}")

    st.audio(audio_file)


    if st.button("🚀 AI 분석 시작", type="primary"):

        with st.spinner("AI가 녹음 내용을 듣고 분석하고 있습니다..."):

            file_extension = os.path.splitext(audio_file.name)[1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_extension
            ) as temp_file:

                temp_file.write(audio_file.getbuffer())
                temp_path = temp_file.name

            try:

                # Gemini 연결
                client = genai.Client(
                    api_key=st.secrets["GEMINI_API_KEY"]
                )

                # 녹음파일 Gemini에 업로드
                uploaded_file = client.files.upload(
                    file=temp_path
                )

                # 녹취 + 분석 요청
                interaction = client.interactions.create(
                    model="gemini-3.7-flash",
                    input=[
                        {
                            "type": "text",
                            "text": """
너는 전문 AI 회의 비서다.

첨부된 녹음파일의 내용을 먼저 정확하게 녹취하고,
그 내용을 기반으로 회의를 분석해라.

중요한 규칙:
- 녹음에서 실제로 말한 내용만 사용한다.
- 없는 내용을 추측하지 않는다.
- 불필요한 잡담과 반복은 요약에서 제외한다.
- 담당자가 명확하지 않으면 '미정'이라고 표시한다.
- 기한이 명확하지 않으면 '미정'이라고 표시한다.
- 중요한 결정사항과 해야 할 일을 빠뜨리지 않는다.
- 결과는 한국어로 작성한다.

아래 형식으로 작성해라.


# 📌 한 줄 요약
회의 전체 내용을 한 문장으로 요약


# 📝 전체 요약
회의의 주요 내용을 이해하기 쉽게 정리


# 🔑 핵심 논의사항
- 주요 논의 내용을 항목별로 정리


# ✅ 결정사항
- 최종적으로 결정된 내용
- 없으면 '없음'


# 📋 해야 할 일

각 업무를 아래 형식으로 정리

- 업무:
- 담당자:
- 기한:


# ❓ 추가 확인사항
- 추가 확인이 필요한 사항
- 결정되지 않은 사항
- 없으면 '없음'


# 📄 전체 녹취록
녹음에서 말한 내용을 가능한 한 빠짐없이 작성
"""
                        },
                        {
                            "type": "audio",
                            "uri": uploaded_file.uri,
                            "mime_type": uploaded_file.mime_type
                        }
                    ]
                )

                st.session_state.result = interaction.output_text

            except Exception as e:

                st.error("AI 분석 중 오류가 발생했습니다.")
                st.error(str(e))

            finally:

                if os.path.exists(temp_path):
                    os.remove(temp_path)


# 결과 표시
if st.session_state.result:

    st.divider()

    st.subheader("🤖 AI 회의 분석 결과")

    st.markdown(st.session_state.result)
