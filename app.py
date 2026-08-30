import streamlit as st
import base64
import tempfile
import os

from google import genai


# --------------------------------------------------
# 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="AI 회의 비서",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ AI 회의 비서")

st.write(
    "녹음파일을 업로드하면 AI가 녹취하고 "
    "회의 내용을 자동으로 정리합니다."
)


# --------------------------------------------------
# 세션 저장
# --------------------------------------------------

if "result" not in st.session_state:
    st.session_state.result = ""

if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = ""


# --------------------------------------------------
# MIME TYPE 확인
# --------------------------------------------------

def get_mime_type(file_name, uploaded_type):

    if uploaded_type:
        return uploaded_type

    extension = os.path.splitext(file_name)[1].lower()

    mime_types = {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".wav": "audio/wav",
        ".mp4": "audio/mp4"
    }

    return mime_types.get(extension, "audio/mpeg")


# --------------------------------------------------
# Gemini 연결
# --------------------------------------------------

def get_client():

    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


# --------------------------------------------------
# AI에게 전달할 명령
# --------------------------------------------------

PROMPT = """
너는 전문적인 AI 회의 비서다.

첨부된 녹음파일을 처음부터 끝까지 듣고,
녹취와 회의 분석을 수행해라.

반드시 한국어로 작성한다.

중요한 규칙:

1. 실제 녹음에서 말한 내용만 사용한다.
2. 녹음에 없는 내용은 절대로 추측하지 않는다.
3. 중요한 업무 내용은 빠뜨리지 않는다.
4. 잡담이나 의미 없는 반복은 요약에서는 제외한다.
5. 담당자가 명확하지 않으면 '미정'이라고 작성한다.
6. 기한이 명확하지 않으면 '미정'이라고 작성한다.
7. 결정되지 않은 내용과 단순 의견을 결정사항으로 작성하지 않는다.
8. 숫자, 날짜, 회사명, 사람 이름, 제품명 등은 가능한 정확하게 작성한다.


아래 형식으로 결과를 작성한다.


# 📌 한 줄 요약

회의 전체 내용을 한 문장으로 요약한다.


# 📝 전체 요약

회의에서 논의된 내용을 이해하기 쉽게 정리한다.


# 🔑 핵심 논의사항

주요 논의사항을 항목별로 작성한다.

- 내용
- 내용
- 내용


# ✅ 결정사항

실제로 최종 결정된 내용만 작성한다.

결정사항이 없으면:

없음


# 📋 해야 할 일

각 업무별로 아래 형식으로 작성한다.

### 업무 1

- 업무:
- 담당자:
- 기한:

### 업무 2

- 업무:
- 담당자:
- 기한:


해야 할 일이 없으면:

없음


# ❓ 추가 확인사항

추가 확인이 필요하거나
아직 결정되지 않은 사항을 작성한다.

없으면:

없음


# 📄 전체 녹취록

녹음에서 실제로 말한 내용을
가능한 한 처음부터 끝까지 빠짐없이 작성한다.

화자가 명확하게 구분되는 경우에는

화자 1:
화자 2:

형태로 구분한다.

화자를 알 수 없는 경우에는
임의로 사람 이름을 만들지 않는다.
"""


# --------------------------------------------------
# 파일 업로드
# --------------------------------------------------

audio_file = st.file_uploader(
    "🎧 녹음파일을 업로드하세요",
    type=["mp3", "m4a", "wav", "mp4"]
)


if audio_file is not None:

    # 새로운 파일이면 이전 결과 삭제
    if st.session_state.uploaded_name != audio_file.name:

        st.session_state.uploaded_name = audio_file.name
        st.session_state.result = ""

    st.success(
        f"업로드 완료: {audio_file.name}"
    )

    st.audio(audio_file)

    file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)

    st.caption(
        f"파일 크기: {file_size_mb:.1f} MB"
    )


    # --------------------------------------------------
    # AI 분석 버튼
    # --------------------------------------------------

    if st.button(
        "🚀 AI 분석 시작",
        type="primary",
        use_container_width=True
    ):

        st.session_state.result = ""

        mime_type = get_mime_type(
            audio_file.name,
            audio_file.type
        )

        try:

            client = get_client()

            with st.status(
                "🤖 AI가 녹음 내용을 분석하고 있습니다...",
                expanded=True
            ) as status:

                status.write(
                    "① 녹음파일을 준비하고 있습니다."
                )

                audio_bytes = audio_file.getvalue()


                # --------------------------------------------------
                # 20MB 미만
                # Gemini에 직접 전달
                # --------------------------------------------------

                if file_size_mb < 20:

                    status.write(
                        "② 녹음파일을 Gemini에 전달했습니다."
                    )

                    audio_base64 = base64.b64encode(
                        audio_bytes
                    ).decode("utf-8")

                    status.write(
                        "③ 녹취 및 회의 분석을 진행하고 있습니다."
                    )

                    interaction = client.interactions.create(
                        model="gemini-3.7-flash",
                        input=[
                            {
                                "type": "text",
                                "text": PROMPT
                            },
                            {
                                "type": "audio",
                                "data": audio_base64,
                                "mime_type": mime_type
                            }
                        ]
                    )


                # --------------------------------------------------
                # 20MB 이상
                # Gemini Files API 사용
                # --------------------------------------------------

                else:

                    status.write(
                        "② 파일 크기가 커서 Gemini 서버에 업로드하고 있습니다."
                    )

                    extension = os.path.splitext(
                        audio_file.name
                    )[1]

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=extension
                    ) as temp_file:

                        temp_file.write(audio_bytes)

                        temp_path = temp_file.name


                    try:

                        uploaded_file = client.files.upload(
                            file=temp_path
                        )

                        status.write(
                            "③ 파일 업로드 완료. 녹취 및 분석을 진행하고 있습니다."
                        )

                        interaction = client.interactions.create(
                            model="gemini-3.7-flash",
                            input=[
                                {
                                    "type": "text",
                                    "text": PROMPT
                                },
                                {
                                    "type": "audio",
                                    "uri": uploaded_file.uri,
                                    "mime_type": (
                                        uploaded_file.mime_type
                                        or mime_type
                                    )
                                }
                            ]
                        )

                    finally:

                        if os.path.exists(temp_path):
                            os.remove(temp_path)


                # --------------------------------------------------
                # 결과 저장
                # --------------------------------------------------

                st.session_state.result = (
                    interaction.output_text
                )

                status.update(
                    label="✅ 분석이 완료되었습니다.",
                    state="complete",
                    expanded=False
                )


        except Exception as e:

            st.error(
                "AI 분석 중 오류가 발생했습니다."
            )

            st.code(str(e))


# --------------------------------------------------
# 결과 표시
# --------------------------------------------------

if st.session_state.result:

    st.divider()

    st.subheader(
        "🤖 AI 회의 분석 결과"
    )

    st.markdown(
        st.session_state.result
    )
