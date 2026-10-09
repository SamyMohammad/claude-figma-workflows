package dev.figma.fixture.core.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.absoluteOffset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import dev.figma.fixture.core.theme.LocalAppTokens

enum class GraphicNode { Home, Review, Button, Card, Badge }

private data class VectorRect(val x: Int, val y: Int, val width: Int, val height: Int)

// Synthetic source geometry in spacing units (8 logical pixels), not app captures.
private fun rectangles(node: GraphicNode): List<VectorRect> = when (node) {
    GraphicNode.Home -> listOf(VectorRect(1, 1, 18, 8), VectorRect(1, 10, 4, 4), VectorRect(1, 14, 18, 6))
    GraphicNode.Review -> listOf(VectorRect(1, 1, 18, 8), VectorRect(14, 10, 4, 4), VectorRect(1, 14, 18, 6))
    GraphicNode.Button -> listOf(VectorRect(1, 7, 18, 6))
    GraphicNode.Card -> listOf(VectorRect(1, 6, 18, 8))
    GraphicNode.Badge -> listOf(VectorRect(8, 8, 4, 4))
}

@Composable
fun GraphicFixture(node: GraphicNode, modifier: Modifier = Modifier) {
    val tokens = LocalAppTokens.current
    Box(modifier.size(tokens.frameSize).background(tokens.colorBackground).testTag("synthetic-graphic-frame")) {
        for (rect in rectangles(node)) {
            Box(Modifier.absoluteOffset(tokens.spaceSmall * rect.x, tokens.spaceSmall * rect.y)
                .size(tokens.spaceSmall * rect.width, tokens.spaceSmall * rect.height)
                .background(tokens.colorPrimary, RoundedCornerShape(tokens.shapeRadius)))
        }
    }
}
