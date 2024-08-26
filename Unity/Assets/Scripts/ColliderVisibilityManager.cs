using UnityEngine;

// This object is necesary in the scene to be able to change the collider visibility
public class ColliderVisibilityManager : MonoBehaviour
{
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.V)) // Press 'V' to toggle visibility
        {
            Agent.ToggleColliderVisibility();
            Debug.Log("Collider visibility toggled: " + (Agent.showColliders ? "On" : "Off"));
        }
    }
}