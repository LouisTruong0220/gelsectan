# Tin nhắn gửi OrionStar — app Gelsectan trên Minibot (01/10/2026)

> Soạn để anh Trường gửi hãng qua Lark. Thông tin máy đọc thẳng từ robot bằng adb ngày 01/10/2026.
> Chỗ `[…]` là việc anh Trường điền trước khi gửi (ngày sự kiện).
> Tin trước gửi hãng về LLM cho Minibot: `../giao-tiep-ai-minibot/gui-orionstar.md` (28/08/2026).

---

Hello OrionStar team,

This is Roboworld (Vietnam). We are preparing a GreetingBot Mini for a medical event of our client
on [event date]. We have built a custom Android app for it and need your help on a few points.

**Robot information**

- Model: OS-R-SD03 (GreetingBot Mini)
- Robot SN: MC1BHW0C170230407107
- Corp ID: orion.ovs.entprise.8159436847
- System build: 20230707 (OrionStarOS 9.2, Android 9)
- App package: vn.roboworld.chibach

**1. AgentOS is not installed on this robot**

The package `com.ainirobot.agentservice` is missing. Only `com.ainirobot.speechasrservice` 1.40.2 is
present, so Agent SDK 0.4.7 cannot bind. Our app needs AgentOS for voice Q&A with the Robot Portal
knowledge base.

- Can you install or upgrade AgentOS for this SN?
- Which ROM version is required, and how can we upgrade a robot that is in Vietnam (OTA or offline package)?
- How long does it usually take?

**2. New appId**

Please issue a new appId for the package `vn.roboworld.chibach` and bind it to our Corp ID.

**3. Robot Portal knowledge base**

Our client's content is medical, and every answer has been approved by the client.

- Is the knowledge base shared by all robots in our enterprise account, or can we limit a document to one appId or one robot?
- Does it support Vietnamese documents well? What are the file size and format limits?
- Can we make AgentOS answer only from the knowledge base, without adding its own information?

**4. Letting the app answer instead of AgentOS**

For questions that match the client's approved Q&A, our app reads the approved answer itself
through `SkillApi.playText`. Right now we stop AgentOS with `AgentCore.stopTTS()` when it starts speaking.

- Is there an official way to tell AgentOS not to answer one turn?
- When planning is on (`isDisablePlan = false`) and `isEnableWakeFree = false`, AgentOS still answers
  conversations around the robot. Is there a setting so it only listens when our app opens the microphone?

**5. Cloud LLM through `queryByText`**

On this robot, `SkillApi.queryByText` still returns an empty `answerText`, and `debug_info` shows
`"chatgpt Not yet open"`. Can you enable it for our account?

**6. Two smaller questions**

- Vietnamese TTS: are there other Vietnamese voices for the Mini? Can we add a pronunciation list for
  product names such as "Gelsectan"?
- Does `startFocusFollow` turn the whole body to face the user on the Mini, as it does on GreetingBot Nova?

Thank you very much. We look forward to your reply.

Best regards,
Roboworld
