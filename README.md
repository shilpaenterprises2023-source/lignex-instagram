# Lignex Instagram auto-posting

Automatic Instagram posts for **Lignex Wood Finishing Studio** (@lignex.woodfinishingstudio), JP Nagar, Bangalore.

## How it works

1. Claude designs posters and writes captions, saves the images in `posts/` and adds them to `queue.json`.
2. Every day at **7:00 pm IST**, GitHub Actions runs `post_to_instagram.py`.
3. The script posts the next poster that is due (its `date` is today or earlier and `status` is `pending`) using Instagram's official API, then marks it `posted`.

Only one post goes out per day. Days with nothing due are skipped.

## One-time setup

Add two secrets under **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|---|---|
| `IG_USER_ID` | Instagram account ID from the Meta developer app |
| `IG_ACCESS_TOKEN` | Instagram long-lived access token |

Never put the token in a file or a chat. It only goes in GitHub secrets.

## Testing

**Actions → Post to Instagram → Run workflow.** Leave "Test only" ticked to check without posting; untick it to post the next due poster right away.

## Queue format

```json
{
  "date": "2026-10-14",
  "image": "posts/2026-10-14-teak-stain.jpg",
  "caption": "Caption text with #hashtags",
  "status": "pending"
}
```

Images: JPEG, 1080×1350 (portrait) or 1080×1080 (square), under 8 MB.

## Token renewal

Instagram long-lived tokens last about **60 days**. Generate a new one in the Meta developer app before it expires and replace the `IG_ACCESS_TOKEN` secret.

## Later: videos (reels)

The script can be extended to post reels by sending `media_type=REELS` with a `video_url` instead of `image_url`.
