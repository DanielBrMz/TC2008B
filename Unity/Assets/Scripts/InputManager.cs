using UnityEngine;

// This object is necesary in the scene to be able to change the collider visibility
public class ColliderVisibilityManager : MonoBehaviour
{
    void Update()
    {   

        if (Input.GetKeyDown(KeyCode.V)) // Press 'V' to toggle visibility
        {
            Agent.ToggleColliderVisibility();
        }

        if (Input.GetKeyDown(KeyCode.T))
        {
            Enviroment.ToggleTileVisibility();
        }

        if (Input.GetKeyDown(KeyCode.C))
        {
            Object.ToggleItemColliderVisibility();
        }
    }
}