using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Object : MonoBehaviour
{   
    [Header("Parameters")]
    public float size = 2f;

    [Header("Prefabs")]
    [SerializeField] private GameObject[] models;

    private static bool itemsVisible = false;

    private bool isGrabbed = false;
    private Transform grabber;

    private bool isBeingGrabbed = false;


    private void Awake()
    {
        transform.localScale = Vector3.one * size;
        SetRandomModel();
    }

    private void Update() {
        UpdateObjectColliderVisibility();
    }

    private void UpdateObjectColliderVisibility()
    {
        transform.GetComponent<Renderer>().enabled = itemsVisible;
    }

    public static void ToggleItemColliderVisibility()
    {
        itemsVisible = !itemsVisible;
    }

    public bool TryStartGrab()
    {
        if (isBeingGrabbed) return false;
        isBeingGrabbed = true;
        return true;
    }

    public void CancelGrab()
    {
        isBeingGrabbed = false;
    }

    public void ObjGrab(Transform newGrabber)
    {
        isGrabbed = true;
        grabber = newGrabber;
        GetComponent<Collider>().enabled = false;
    }

    // This function is temporal while I figure stacks out
    public void ObjDrop()
    {{
        isGrabbed = false;
        grabber = null;
        GetComponent<Collider>().enabled = true;
    }}

    public void SetRandomModel()
    {
        if (models.Length > 0)
        {
            int randomIndex = Random.Range(0, models.Length);
            GameObject selectedModel = Instantiate(models[randomIndex], transform);
            selectedModel.transform.localPosition = Vector3.zero;
            selectedModel.layer = LayerMask.NameToLayer("Objects");
        }
    }

    private void LateUpdate() {
        if (isGrabbed && grabber != null)
        {
            transform.position = grabber.position + Vector3.up * (size / 2);
        }
    }
}